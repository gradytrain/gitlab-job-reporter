#!/usr/bin/env python

import logging
import argparse
import requests
import os
from pathlib import Path
from jinja2 import Template
import codecs
from datetime import datetime, timedelta

HEADERS = {"Authorization": "Bearer {0}".format(os.getenv("GITLAB_PAT"))}
END_LOG_NO_ERROR = "Logging stopped, Reason: exit code 0"
END_LOG_ERROR = "Logging stopped, Reason: Error"

project_path = os.path.dirname(os.path.abspath(__file__))

# setup logging
now = datetime.now()
timestamp = now.strftime('%m-%d-%Y-%H%M')
logger = logging.getLogger(__name__)
script_name = "nightly-job-reporter"
log_name = "{0}-runtime-logs-{1}.log".format(script_name, timestamp)
if os.getenv("CI"):
    log_path = log_name
else:
    log_path = '{0}/logs/{1}'.format(project_path, log_name)
logging.basicConfig(filename=log_path, level=logging.INFO)
logger.info('Logging Start for package utility script')


def output_and_log_message(message, exception=False):
    if exception is False:
        logging.info(message)
        print(message)
    else:
        logging.error(message)
        logging.info(END_LOG_ERROR)
        raise Exception(message)


# Get arguments
parser = argparse.ArgumentParser()
parser.add_argument('--url', '-u', required=True, help="base url or the ci api url")
args = parser.parse_args()

logging.info("Using url: %s" % args.url)
projects = []
repoconfig_file_path = "%s/.repoconfig" % project_path
# get projects listing
if os.path.exists(repoconfig_file_path):
    logging.info("Found repos file")
    with open(repoconfig_file_path, "r") as repos_file:
        projects = repos_file.read().splitlines()
    if not projects:
        output_and_log_message("Repos file was empty, please add project names and try again", exception=True)
else:
    output_and_log_message(".repoconfig file could not be found in project directory")

logging.info("getting reports for these projects: %s" % projects)


def get_project_id(project_name):
    project_request = requests.get("{0}/projects/?search={1}".format(args.url, project_name), headers=HEADERS, timeout=5)
    if project_request.status_code != 200:
        output_and_log_message("Getting project ID was not 200, was: %s" % project_request.status_code)
    else:
        projects = project_request.json()
        for project in projects:
            if project['path'] == project_name:
                return project['id']


night_runs = []
# Get outputs
for project in projects:
    # get project ids
    id = get_project_id(project)

    # with project id, get all the project pipelines
    pipelines_request = requests.get("{0}/projects/{1}/pipelines".format(args.url, id), headers=HEADERS, timeout=5)
    if pipelines_request.status_code != 200:
        output_and_log_message("Getting pipelines request was not 200, was: %s" % pipelines_request.status_code)
    else:
        pipelines = pipelines_request.json()
        scheduled_pipelines = []
        # list comprehension to get scheduled pipelines and take first one which should be last scheduled one
        for pipeline in pipelines:
            if pipeline['source'] == "schedule":
                scheduled_pipelines.append(pipeline)

        night_runs.append(scheduled_pipelines[0])

reports = []
# create the report dictionary object
for run in night_runs:
    project_request = requests.get("{0}/projects/{1}".format(args.url, run['project_id']), headers=HEADERS, timeout=5)
    if project_request.status_code != 200:
        output_and_log_message("Request for project name was not 200, was: %s" % project_request.status_code)
    else:
        dtobj = datetime.strptime(run['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        report_timestamp = dtobj.strftime('%m-%d-%Y')
        nice_time = (dtobj + timedelta(hours=-5)).strftime('%m-%d-%Y - %I:%M %p')
        # assemble report object
        report = {
            'proj_name': project_request.json()['name'],
            'proj_id': run['project_id'],
            'id': run['id'],
            'status': run['status'],
            'created_at': nice_time,
            'url': run['web_url']
        }
        reports.append(report)

# create file using jinja2 template
with open('%s/template.md' % project_path, 'r') as file:
    template = Template(file.read(), trim_blocks=True)
rendered_file = template.render(reports=reports)

# output the file in the respective week and with a nice timestamp
file_path = "{0}/reports/week{1}".format(project_path, datetime.now().isocalendar().week)
Path(file_path).mkdir(parents=True, exist_ok=True)
report_title = "Nightly_Run_Report_%s.md" % report_timestamp
fq_path = os.path.join(file_path, report_title)
output_file = codecs.open(fq_path, "w", "utf-8")
output_file.write(rendered_file)
output_file.close()

logging.info(END_LOG_NO_ERROR)
exit(0)
