# -*- coding: utf-8 -*-

"""
Misc. utilities handling input/output streams
"""

import json
import logging
import os
import string
import sys

logger = logging.getLogger(__name__)
REFRESH_PROGRESS_EVERY_N_CYCLES = 1000
VIRTUAL_CURRENCIES = ['LTC', 'SLL', 'WMZ']


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

        return {'data': database, 'file_name': file_name_without_extension}

    except IOError, e:
        #if user mistyped database path ask her again
        logger.error('IOError: ' + str(e))
        loadUserSpecifiedDatabase()

    except:
        raise


def createFolder(_folder_path):
    """
    Creates a directory if it doesn't already exist.

    :param _folder_path: relative path of the folder
    :return: Nothing. Side effects: creates a folder on the disk.
    """
    try:
        logger.info('createFolder: Creating folder: %s' % _folder_path)

        if not os.path.exists(_folder_path):
            os.makedirs(_folder_path)

    except:
        raise


def getDatabaseCurrency(_file_name):
    """
    Retrieves currency and market name from file path.

    :param _file_name: (string) path of the file
    :return: (dict) market name and currency
    """
    try:
        #parse file name
        market_name = _file_name[string.rfind(_file_name, "/") + 1: string.rfind(_file_name, ".json")]
        currency = market_name[-3:]

        return {'market_name': market_name, 'currency': currency}

    except:
        raise


def listFiles(_db_dir_path):
    """
    Lists file names.

    Lists absolute paths of files contained in folder
    :param _db_dir_path: (string) path to folder of interest
    :return: (list) all file names in folder
    """
    try:
        logger.info('listFiles: Obtaining list of files in folder: %s' % _db_dir_path)

        #list files: holds paths of found files in directory
        file_names_ = []

        #list files
        files = os.listdir(_db_dir_path)

        for file_name in files:
            #exclude virtual currencies
            currency = getDatabaseCurrency(file_name)['currency']

            if currency not in VIRTUAL_CURRENCIES:
                file_names_.append(_db_dir_path + '/' + file_name)

        return file_names_

    except:
        raise


def serializeData(_file_path, _data):
    """
    Serializes data to JSON.

    :param _file_path: (string) path of saved data
    :param _data: (list) data to be saved
    :return: Nothing. Side effects: saves data to disk.
    """
    try:
        #get data size
        size = len(_data)
        logger.debug('serializeData: Data size: %s' % size)

        if size:
            logger.info('serializeData: Saving data to: %s' % _file_path)

            with open(_file_path, 'w') as f:
                json.dump(_data, f)

        else:
            logger.warning('serializeData: No data in container, %s will not be saved' % _file_path)

    except:
        raise