#!/usr/bin/env python

import logging
import os
from pathlib import Path
from datetime import datetime, timedelta

class MyLogger:
    END_LOG_NO_ERROR = "Logging stopped, Reason: exit code 0"
    END_LOG_ERROR = "Logging stopped, Reason: Error"

    def __init__(self, script_name, log_level=logging.INFO):
        self.script_name = script_name
        self.now = datetime.now()
        self.timestamp = self.now.strftime('%m-%d-%Y-%H%M')

        # path determination
        self.project_path = os.getcwd() # get script run directory
        self.log_name = "{0}-runtime-logs-{1}.log".format(self.script_name, self.timestamp)

        # project_path = os.path.dirname(os.path.abspath(__file__))
        # logger = logging.getLogger(__name__)

        if os.getenv("CI"):
            self.log_path = self.log_name
        else:
            log_dir = os.path.join(self.project_path, 'logs')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            self.log_path = os.path.join(log_dir, self.log_name)



            # log_path = '{0}/logs/{1}'.format(project_path, log_name)

        # Configure Logging
        logging.basicConfig(filename=self.log_path, level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(self.script_name)
        self.logger.info('Logging Start for %s' % self.script_name)


    def log(self, message, exception=False):
        if exception is False:
            self.logger.info(message)
            print(message)
        else:
            self.logger.error(message)
            self.logger.info(self.END_LOG_ERROR)
            raise Exception(message)

    def stop_success(self):
        self.logger.info(self.END_LOG_NO_ERROR)
