# -*- coding: utf-8 -*-

import logging
import logging.handlers
import lib.io as tools


def getCustomLogger(_file_name, _logging_level):
    """
    Creates a logger instance and configures it.

    A logger instance is created configured to write to console and a file which is rotated every N bytes.

    :param _file_name: (string) name of the logging file
    :param _logging_level: (int) level of logging i.e. logging.INFO, logging.DEBUG etc.
    :return: (object) logger instance
    """
    try:
        logger = logging.getLogger()
        logger.setLevel(_logging_level)

        log_dir = 'logs/'
        tools.createFolder(log_dir)

        #configure file handler for the logger
        log_name = _file_name.split(".")[0]
        log_file_name = log_dir + log_name + '.log'
        fh = logging.handlers.RotatingFileHandler(log_file_name, maxBytes=1000000, backupCount=1)
        fh.setLevel(_logging_level)

        #create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)

        #create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s;%(levelname)s;%(name)s.%(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        #add handlers to the logger
        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger

    except:
        raise