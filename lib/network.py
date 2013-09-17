# -*- coding: utf-8 -*-

"""
Functions handling network requests
"""

import httplib
import logging
import re
import time
import urllib2

logger = logging.getLogger(__name__)
URL_CALCULATOR = 'http://www.google.com/ig/calculator?hl=en&q='
BASE_CURRENCY = 'USD'
MAXIMUM_RECONNECTIONS = 3
PAUSE_BETWEEN_RECONNECTIONS = 3


def getHtml(_url):
    """
    Retrieves requested resource on url.

    :param _url: (string) address of requested HTML
    :return: (string) html text
    """
    try:
        logger.info('getHtml: Requesting: %s' % _url)

        response = urllib2.urlopen(_url)

        #download data
        html_ = response.read()
        logger.debug('getHtml: Retrieved data: %s' % html_)

        return html_

    except urllib2.HTTPError, e:
        logger.error('getHtml: HTTPError: ' + str(e.code))

    except urllib2.URLError, e:
        logger.error('getHtml: URLError: ' + str(e.reason))

    except httplib.HTTPException, e:
        logger.error('getHtml: HTTPException: ', str(e))

    except Exception:
        logger.exception('getHtml: Unhandled exception: ')


def downloadExchangeRates(_source_currency, _track_reconnections):
    """
    Downloads exchange rate for given currency.

    :param _source_currency: (string) currency other than USD
    :param _track_reconnections: (map) tracks how many times we have already reconnected
    :return: (float) exchange rate for requested currency. Side effect: _track_reconnections is being changed.
    """
    try:
        logger.info('downloadExchangeRates: Retrieving exchange rates.')
        logger.debug('downloadExchangeRates: Retrieving exchange rates for: %s' % _source_currency)

        exchange_rate_ = 0

        #download exchange rate
        got_html = getHtml(URL_CALCULATOR + '1' + _source_currency + '=?' + BASE_CURRENCY)

        #parse
        if got_html:
            if 'error: ""' in got_html:
                #parse data
                re_object = re.search(".*rhs: \"(\d\.\d*)", got_html)

                #using float since we're not interested in high precision
                exchange_rate_ = float(re_object.group(1))
                logger.debug('downloadExchangeRates: Parsed exchange rate: %s' % exchange_rate_)

            else:
                #reconnect if error field not empty
                if _track_reconnections['times_reconnected'] <= MAXIMUM_RECONNECTIONS:
                    logger.debug('downloadExchangeRates: Times reconnected: %s' %
                                 _track_reconnections['times_reconnected'])
                    logger.warning('downloadExchangeRates: Server signalizes an error, repeating request.')

                    _track_reconnections['times_reconnected'] += 1

                    #wait for the server to allow another inquiry
                    time.sleep(PAUSE_BETWEEN_RECONNECTIONS)

                    #repeat request
                    downloadExchangeRates(_source_currency, _track_reconnections)

                else:
                    logger.error('downloadExchangeRates: Could not obtain exchange rate for: %s, returning '
                                 'default value.' % _source_currency)

        return exchange_rate_

    except:
        raise