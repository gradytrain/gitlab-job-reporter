#!/usr/bin/env python

import logging
import argparse
import requests
import os
from pathlib import Path
from jinja2 import Template
import codecs
from datetime import datetime, timedelta

headers = {"Authorization": "Bearer {0}".format(os.getenv("GITLAB_PAT"))}

# setup logging
now = datetime.datetime.now()
timestamp = now.strftime('%m-%d-%Y-%H%M')
logger = logging.getLogger(__name__)
log_name = "package-utility-runtime-logs-%s.log" % timestamp
if os.getenv("CI"):
    log_path = log_name
else:
    logp_ath = 'logs/%s' % log_name
logging.basicConfig(filename=log_path, level=logging.INFO)
logger.info('Logging Start for package utility script')

# Get arguments
parser = argparse.ArgumentParser()
parser.add_argument('--url', '-u', required=True, help="base url or the ci api url")
args = parser.parse_args()

logging.info("Using url: %s" % args.url)
projects = []
# get projects listing
if os.path.exists("repos.txt"):
    logging.info("Found repos.txt file")
    with open("repos.txt", "r") as repos_file:
        for project in repos_file:
            projects.append(project)
else:
    message = "repos.txt file could not be found in project directory"
    logging.error(message)
    raise Exception(message)

logging.info("getting reports for these projects: %s" % projects)

def get_project_id(project_name):
    project_request = requests.get(args.url+"/projects/?search=%s" % project_name, headers=headers, timeout=5)
    if project_request.status_code != 200:
        print("Was not 200, was: %s" % project_request.status_code)
        exit(1)
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
    pipelines_request = requests.get(args.url+"/projects/%s/pipelines" % id, headers=headers, timeout=5)
    if pipelines_request.status_code != 200:
        print("Was not 200, was: %s" % pipelines_request.status_code)
        exit(1)
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
    project_request = requests.get(args.url+"/projects/%s" % run['project_id'], headers=headers, timeout=5)
    if project_request.status_code != 200:
        print("Was not 200, was: %s" % project_request.status_code)
        exit(1)
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
with open('template.md', 'r') as file:
    template = Template(file.read(), trim_blocks=True)
rendered_file = template.render(reports=reports)

# output the file in the respective week and with a nice timestamp
file_path = "reports/week%s" % datetime.now().isocalendar().week
Path(file_path).mkdir(parents=True, exist_ok=True)
report_title = "Nightly_Run_Report_%s.md" % report_timestamp
fq_path = os.path.join(file_path, report_title)
output_file = codecs.open(fq_path, "w", "utf-8")
output_file.write(rendered_file)
output_file.close()
