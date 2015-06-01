# -*- coding: utf-8 -*-

"""
Misc. utilities handling input/output streams
"""

import json
import logging
import os
import string
import sys
from lib import constants
logger = logging.getLogger(__name__)
REFRESH_PROGRESS_EVERY_N_CYCLES = 1000



def displayProgress(_loop_index, _size_to_process, accuracy):
    try:
        if _loop_index % REFRESH_PROGRESS_EVERY_N_CYCLES == 0:
            progress_percent = float(_loop_index) / float(_size_to_process) * 100

            sys.stdout.write('%.5f%%, predicted_energy_in(#s=0) = %.5f, predicted_energy_out(#s>0) = %.5f\n'
                             % (progress_percent, accuracy['global_statistics']['predicted_energy_in'],
                                accuracy['global_statistics']['predicted_energy_out']))

    except:
        raise


def loadUserSpecifiedDatabase():
    try:
        logger.info('loadUserSpecifiedDatabase: Requesting user input.')

        database_file_name = raw_input('Path to market data you wish to simulate: ')
        logger.debug('loadUserSpecifiedDatabase: User input: %s' % database_file_name)

        #load the data
        with open(database_file_name, 'r') as f:
            database = json.load(f)

        file_name_without_extension = database_file_name.split('.')[0]

        return database, file_name_without_extension

    except IOError, e:
        #if user mistyped database path ask her again
        logger.error('IOError: ' + str(e))
        loadUserSpecifiedDatabase()

    except:
        raise


def create_folder(path):
    logger.info("%s", path)

    if not os.path.exists(path):
        os.makedirs(path)


def parse_currency(fn):
    """
    Parses currency and market name from file path.

    :param fn: (string) path of the file
    :return: (market name, currency)
    """
    market_name = fn[string.rfind(fn, "/") + 1: string.rfind(fn, constants.db.EXTENSION)]
    currency = market_name[-3:]

    logger.debug("For file name=%s parsed market_name=%s, currency=%s", fn, market_name, currency)
    return market_name, currency


def list_files(dir_path):
    """
    Lists absolute paths of files contained in folder
    :rtype: list
    """
    # list files: holds paths of found files in directory
    abs_fn = []

    for file_name in os.listdir(dir_path):
        market_name, currency = parse_currency(file_name)

        if currency not in constants.currency.IGNORED:
            abs_fn.append(dir_path + file_name)

    logger.debug("In %s found: %s", dir_path, abs_fn)
    return abs_fn


def serialize_data(path, data):
    """
    Serializes data to JSON.

    :param path: (string) path of saved data
    :param data: (list) data to be saved
    """
    if data:
        logger.info('serializeData: Saving data to: %s' % path)

        with open(path, 'w') as f:
            json.dump(data, f)

    else:
        logger.warning('serializeData: No data in container, %s will not be saved.' % path)
