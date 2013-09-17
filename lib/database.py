# -*- coding: utf-8 -*-

"""
Functions to construct and normalize database
"""

import json
import heapq
import logging
import time
import lib.io as io
import lib.network as net

logger = logging.getLogger(__name__)
URL_TRADES = 'http://bitcoincharts.com/t/trades.csv?symbol='
URL_EXCHANGES = 'http://bitcoincharts.com/t/markets.json'
PAUSE_BETWEEN_RECONNECTS = 3


################################
#database construction functions
################################
def _getAllMarkets():
    """
    Retrieves all available markets.

    bitcoincharts.com offers a JSON of current status (high, low, etc.) for every available market. From this data
    we extract only market names.
    :return: (list) all available markets
    """
    try:
        logger.info('getAllMarkets: Retrieving available markets.')

        #get markets: holds available markets
        markets_ = []

        #send request
        got_html = net.getHtml(URL_EXCHANGES)

        #parse
        if got_html:
            data = json.loads(got_html)

            #from all the data get only market name
            for dic in data:
                currency = dic['symbol']

                markets_.append(currency)

        return markets_

    except:
        raise


def _getTrades(_market):
    """
    Downloads market data for requested market.

    Downloads market data in CSV format. Example data string to parse:
    "1340234323,5.407670000000,0.990600000000 1340236726,5.407670000000,3.000000000000"
    :param _market: (string) market name
    :return: (list) a list of trades e.g. [[1340234323,5.407670000000,0.990600000000], [...], ...]
    """
    try:
        logger.info('getTrades: Retrieving trade data for: %s' % _market)

        #getting market trades: holds all trade events from the market
        trades_ = []

        #get data from the beginning of the market existence
        got_html = net.getHtml(URL_TRADES + _market + '&start=0')

        #parse data
        if got_html:
            #split by spaces
            html_sets = got_html.split()
            logger.debug('getTrades: Parsing: %s' % html_sets)

            #parse fields to float since we're not interested in high precision
            for sets in html_sets:
                data_set = sets.split(",")
                data_set_float = []

                #parse fields to float
                for field in data_set:
                    number_field = float(field)
                    data_set_float.append(number_field)
                trades_.append(data_set_float)

        return trades_

    except:
        raise


def createDatabase(_database_folder):
    """
    Downloads trading data for available markets and saves it to a folder.

    Downloads historical trading data with the highest resolution available and serializes it. It is recommended
     to pause between downloads to not trigger server's DDOS filter.
    :param _database_folder: (string) name of the folder where market data is to be saved
    :return: Nothing. Side effects: Writes data to disk.
    """
    try:
        logger.info('createDatabase: Building database.')

        #get all available markets
        markets = _getAllMarkets()

        #retrieve market data
        for market in markets:
            logger.debug('createDatabase: Processing: %s' % market)

            #get data
            print "Retrieving data for market: ", market
            trades = _getTrades(market)

            #save the data
            file_path = _database_folder + '/' + market + ".json"
            io.serializeData(file_path, trades)

            #don't get banned by the server
            time.sleep(PAUSE_BETWEEN_RECONNECTS)

    except:
        raise


#################################
#database normalization functions
#################################
def _normalize(_file_name, _exchange_rate):
    """
    Normalizes prices to USD.

    Converts market prices from non-USD markets to USD.
    :param _file_name: (string) name of the file being processed
    :param _exchange_rate: (float) rate relative to USD
    :return: (list) normalized data
    """
    try:
        logger.info('normalize: Normalizing market data.')

        #read market data
        logger.debug('normalize: Processing: %s with exchange rate: %s' % (_file_name, _exchange_rate))
        with open(_file_name, 'r') as f:
            data = json.load(f)

            #normalize prices relative to USD
            for lst in data:
                #format of lst is [unix_time, price_original_currency, amount]
                lst[1] *= _exchange_rate

            normalized_data_ = data

        return normalized_data_

    except:
        raise


def _prepareDataForSorting(_hq, _normalized_data, _market_name):
    """
    Prepares data and injects it to heap queue

    Expands tuple with market name and appends the data to heap queue where it is gets sorted by first element in
    the tuple.
    :param _hq: (heapq) heap queue containing data tuples
    :param _normalized_data: (list) market data normalized to USD
    :param _market_name: (string) name of the market that is being processed
    :return: Nothing. Side effect: _hq is being changed.
    """
    try:
        logger.info('prepareDataForSorting: Pushing data to heap queue.')

        for entry in _normalized_data:
            logger.debug('prepareDataForSorting: Processing: %s' % entry)

            #since all in one huge list, append index so we know where it came from
            entry.append(_market_name)

            #our tuple has now the form [unix time, price, amount, market name]
            tpl = tuple(entry)

            #tuple gets sorted by first element
            heapq.heappush(_hq, tpl)

    except:
        raise


def _getOrderedData(_hq):
    """
    Orders data in ascending form.
    :param _hq: (heapq) heap of tuples to be ordered
    :return: (list) ordered data. Side effect: _hq is being changed.
    """
    try:
        logger.info('getOrderedData: Ordering data.')

        #ordering values: holds ordered tuples
        ordered_data_ = []

        for i in range(len(_hq)):
            #retrieve and delete the smallest element
            smallest_entry = heapq.heappop(_hq)
            ordered_data_.append(smallest_entry)

        return ordered_data_

    except:
        raise


def getNormalizedOrderedData(_market_file_names):
    """
    Normalize prices from foreign markets to USD.

    Prices from non USD currencies are converted to USD.
    :param _market_file_names: (list) of absolute paths of saved market data
    :return: (list) normalized and ordered data
    """
    try:
        logger.info('getNormalizedOrderedData: Normalizing and ordering market data.')

        #sorting values: holds values to be sorted using heap queue
        hq = []

        #unique requests to the server: holds rates that we already downloaded
        downloaded_rates = {}

        for file_name in _market_file_names:
            logger.debug('getNormalizedOrderedData: Processing: %s' % file_name)
            print 'Processing: ', file_name

            parsed_file_name = io.getDatabaseCurrency(file_name)
            currency = parsed_file_name['currency']

            #get exchange rate for currency
            #don't send duplicated requests
            if currency in downloaded_rates:
                exchange_rate = downloaded_rates[currency]
            else:
                #keep track of reconnections: holds an index of how many times we have already sent the same request
                track_reconnections = {'times_reconnected': 0}
                exchange_rate = net.downloadExchangeRates(currency, track_reconnections) if currency != 'USD' else 1.0
                downloaded_rates[currency] = exchange_rate

            #include and process only data with valid exchange rate
            if exchange_rate:
                normalized_data = _normalize(file_name, exchange_rate)
                _prepareDataForSorting(hq, normalized_data, parsed_file_name['market_name'])

        ordered_data_ = _getOrderedData(hq)

        return ordered_data_

    except:
        raise