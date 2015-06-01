# -*- coding: utf-8 -*-
__author__ = "Jernej Makovšek"

"""
Functions handling network requests
"""

import httplib
import logging
import re
import time
import urllib2
from lib import constants

logger = logging.getLogger(__name__)


def get_html(url):
    """
    Retrieves requested resource on url.

    :param url: (string) address of requested HTML
    :return: (string) html text
    """
    try:
        logger.info("%s", url)

        response = urllib2.urlopen(url)

        # download data
        html = response.read()

        logger.debug("got: %s", html)
        return html
    except urllib2.HTTPError as e:
        logger.error("HTTPError: " + str(e.code))
    except urllib2.URLError as e:
        logger.error("URLError: " + str(e.reason))
    except httplib.HTTPException as e:
        logger.error("HTTPException: ", str(e))


def download_exchange_rates(currency_symbol, reconnections=0):
    """
    Downloads exchange rate for given currency.

    Since we need the rate only for normalization, we don't need historical or accurate rates. A representable estimate
    is enough.
    :param currency_symbol: (string) currency other than USD
    :param reconnections: (map) tracks how many times we have already reconnected
    :return: (float) exchange rate for requested currency. Side effect: _track_reconnections is being changed.
    """
    exchange_rate = 0

    # download exchange rate
    html_response = get_html(
        constants.url.CALCULATOR + "1" + currency_symbol + "=?" + constants.currency.BASE_CURRENCY
    )

    if html_response:
        if 'error: ""' in html_response:
            # parse data
            re_object = re.search(".*rhs: \"(\d\.\d*)", html_response)

            # using float since we're not interested in high precision
            exchange_rate = float(re_object.group(1))

        else:
            # reconnect if error field not empty
            if reconnections <= constants.url.MAXIMUM_RECONNECTIONS:
                logger.warning("Server signalizes an error, repeating request no.:", reconnections)

                reconnections += 1

                #  wait for the server to allow another inquiry
                time.sleep(constants.url.PAUSE_BETWEEN_RECONNECTS)

                download_exchange_rates(currency_symbol, reconnections)
            else:
                logger.error("Could not obtain exchange rate for: %s", currency_symbol)

    logger.debug("exchange_rate=%s", exchange_rate)
    return exchange_rate
