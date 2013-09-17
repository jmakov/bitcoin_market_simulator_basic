# -*- coding: utf-8 -*-

"""
Exception handlers
"""

import sys


def handleKeyboardInterrupt(_logger):
    """
    Handle exception raised when user sends KeyboardInterrupt.

    :param _logger: (object) selected logger
    :return: Nothing.
    """
    #log event
    msg = '\nReceived KeyboardInterrupt, exiting.'
    _logger.info(msg)

    #notify the user of action taken
    print msg
    sys.exit()


def handleException(_logger):
    """
    Handles general exception.

    :param _logger: (object) selected logger
    :return: Nothing.
    """
    _logger.exception('Unhandled exception: ')