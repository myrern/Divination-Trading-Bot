import logging as log
import os


class LogManager:
    def __init__(self):
        self.log = log

    def create_log_directory(self, log_directory):
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

    def log_info(self, message):
        self.log.info(message)

    def log_error(self, message):
        self.log.error(message)

    def log_warning(self, message):
        self.log.warning(message)

    def log_critical(self, message):
        self.log.critical(message)

    

