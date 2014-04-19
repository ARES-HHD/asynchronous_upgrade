#!/usr/bin/env python
# encoding: utf-8
#
# This script is a module for logging
#

import logging
import logging.handlers
import os.path
import threading

class Logging(object):
    lock = threading.Lock()
    def __init__(self, log_name ,logger_name):
        log_dir = os.path.dirname(log_name)
        if log_dir:
            if not os.path.exists(log_dir):
                raise Exception("init Logging fail: %s log dir not exist" % log_dir)

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

        keep_days = 15 #the old 15 log files will be keeped
        self.file_handler = logging.handlers.TimedRotatingFileHandler(log_name, 'D', 1, keep_days)
        self.file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)

    def __del__(self):
        self.file_handler.close()

    def get_log(self):
        return self.logger

    @classmethod
    def instance(cls, *args, **kwargs):
        cls.lock.acquire()
        try:
            if not hasattr(cls, "_instance"):
                cls._instance = cls(*args, **kwargs)
            return cls._instance
        finally:
            cls.lock.release()
