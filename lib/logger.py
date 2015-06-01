# -*- coding: utf-8 -*-
__author__ = "Jernej Makovšek"

import logging
import logging.handlers
from lib import io, constants


def get_custom_logger(file_name, logging_level):
    """
    A logger instance is created configured to write to console and a file which is rotated every N bytes.

    :param file_name: (string) name of the logging file
    :param logging_level: (int) level of logging i.e. logging.INFO, logging.DEBUG etc.
    :return: (object) logger instance
    """
    logger = logging.getLogger()
    logger.setLevel(logging_level)

    io.create_folder(constants.log.DIR)

    # configure file handler for the logger
    log_name = file_name.split(".")[0]
    fh = logging.handlers.RotatingFileHandler(
        filename=constants.log.DIR + log_name + constants.log.EXTENSION,
        maxBytes=constants.log.MAX_SIZE,
        backupCount=constants.log.BACKUP_COUNT
    )
    fh.setLevel(logging_level)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)

    # create formatter and add it to the handlers
    formatter = logging.Formatter(constants.log.FORMAT)
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info("Logger configured.")
    return logger
