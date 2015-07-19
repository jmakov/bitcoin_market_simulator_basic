#!/usr/bin/env python
"""
Prepares the environment and installs dependencies in virtualenv.
"""

import os
import sys

# append path so we can import project modules
PROJECT_ROOT_PATH = os.path.dirname(os.path.abspath(__file__)) + "/../"
sys.path.append(PROJECT_ROOT_PATH)

from lib import constants, io, log
import commands
import subprocess

logger = log.get_custom_logger(os.path.basename(__file__), constants.log.LEVEL)
VIRTENV_PATH = PROJECT_ROOT_PATH + constants.virtualenv.PATH


def set_up_directories():
    io.create_folder(PROJECT_ROOT_PATH + constants.log.PATH)
    io.create_folder(PROJECT_ROOT_PATH + constants.db.PATH)
    io.create_folder(VIRTENV_PATH)


def _install(package_name):
    logger.info(package_name)

    # using subprocess instead of pip.main(['install', package_name]) because subprocess installs the pck in the right
    # virtenv which we have previously activated
    p = subprocess.Popen([constants.virtualenv.PIP_COMMAND, constants.virtualenv.PIP_ARGUMENT, package_name],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = p.communicate()

    if stdout:
        logger.info(stdout)
    if stderr:
        logger.error(stderr)

    if p.returncode != 0:
        raise EnvironmentError("There was an error when installing dependencies. Please check pip log.")


def update_virtenv():
    with open(PROJECT_ROOT_PATH + constants.virtualenv.REQUIREMENTS_FILE, "r") as f:
        packages = f.readlines()
        logger.info(packages)

    for package in packages:
        print "Installing %s" % package
        _install(package)


if __name__ == "__main__":
    print "Setting up directories."
    set_up_directories()

    print "Creating virtualenv."
    init_virtualenv = constants.virtualenv.COMMAND + " %s" % VIRTENV_PATH
    exit_code, result = commands.getstatusoutput(init_virtualenv)

    if exit_code != 0:
        print "Failed to set up basic virtualenv."
        raise RuntimeError

    print "Updating virtual environment packages."
    # doing execfile() on this file will alter the current interpreter's
    # environment so you can import libraries in the virtualenv
    activate_this_file = VIRTENV_PATH + constants.virtualenv.ACTIVATE_THIS_PATH
    execfile(activate_this_file, dict(__file__=activate_this_file))
    update_virtenv()

    print "Setup completed."
