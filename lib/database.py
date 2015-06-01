# -*- coding: utf-8 -*-
__author__ = "Jernej Makovšek"

"""
Functions to construct and normalize database
"""

try:
    import ujson as json
except ImportError:
    import json
import heapq
import logging
import time
from lib import io, network, constants

logger = logging.getLogger(__name__)


def _get_all_market_symbols():
    """
    Retrieves all available markets.

    bitcoincharts.com offers a JSON of current status (high, low, etc.) for every available market. From this data
    we extract only market names.
    :return: (list) all available markets
    """
    markets = []

    response = network.get_html(constants.url.MARKETS)

    data = json.loads(response)

    # from all the data get only market names
    for dic in data:
        currency = dic['symbol']

        markets.append(currency)

    logger.debug(markets)
    return markets


def _get_trades(market_symbol):
    """
    Downloads market data for requested market.

    Downloads market data in CSV format. Example data string to parse:
    "1340234323,5.407670000000,0.990600000000 1340236726,5.407670000000,3.000000000000"
    :param market_symbol: (string) market name
    :return: (list) a list of trades e.g. [[1340234323,5.407670000000,0.990600000000], [...], ...]
    """
    trades = []

    # get data from the beginning of the market existence
    html_response = network.get_html(constants.url.TRADES + market_symbol + '&start=0')

    # split by spaces
    html_sets = html_response.split()

    # parse fields to float since we're not interested in high precision
    for sets in html_sets:
        data_set = sets.split(",")
        data_set_float = []

        for field in data_set:
            number_field = float(field)
            data_set_float.append(number_field)
        trades.append(data_set_float)

    return trades


def create_database(database_folder):
    """
    Downloads trading data for available markets and saves it to a folder.

    Downloads historical trading data with the highest resolution available and serializes it. It is recommended
    to pause between downloads to not trigger server's DDOS filter.
    :param database_folder: (string) name of the folder where market data is to be saved
    """
    io.create_folder(database_folder)

    # get all available markets
    markets = _get_all_market_symbols()

    # retrieve market data
    for market in markets:
        logger.debug("Processing: %s", market)

        print "Retrieving data for market: ", market
        trades = _get_trades(market)

        io.serialize_data(
            path=database_folder + market + constants.db.EXTENSION,
            data=trades
        )

        # don't get banned by the server
        time.sleep(constants.url.PAUSE_BETWEEN_RECONNECTS)


def _normalize_prices(file_name, exchange_rate):
    """
    Normalizes prices to USD.

    Converts market prices from non-USD markets to USD.
    :param file_name: (string) name of the file being processed
    :param exchange_rate: (float) rate relative to USD
    :return: (list) normalized data
    """
    logger.debug("file_name=%s, exchange_rate=%s")

    with open(file_name, 'r') as f:
        data = json.load(f)

        # normalize prices relative to USD
        for lst in data:
            # format of lst is [unix_time, price_original_currency, amount]
            lst[1] *= exchange_rate     # note again that we're only interested in a representable precision

    return data


def _preprocess_data(hq, normalized_data, market_name):
    """
    Prepares data and injects it to heap queue

    Expands tuple with market name and appends the data to heap queue where it is gets sorted by first element in
    the tuple.
    :param hq: (heapq) heap queue containing data tuples
    :param normalized_data: (list) market data normalized to USD
    :param market_name: (string) name of the market that is being processed
    :return: Nothing. Side effect: hq is changed.
    """
    for entry in normalized_data:
        logger.debug("Processing: %s", entry)

        # since all in one huge list, append index so we know where it came from
        entry.append(market_name)

        # our tuple has now the form [unix time, price, amount, market name]
        tpl = tuple(entry)

        # tuple gets sorted by first element
        heapq.heappush(hq, tpl)


def _get_ordered_data(hq):
    """
    Orders data in ascending form.
    :param hq: (heapq) heap of tuples to be ordered
    :return: (list) ordered data. Side effect: hq is changed.
    """
    # ordering values: holds ordered tuples
    ordered_data_ = []

    for i in range(len(hq)):
        # retrieve and delete the smallest element
        smallest_entry = heapq.heappop(hq)
        ordered_data_.append(smallest_entry)

    return ordered_data_


def get_normalized_ordered_data(file_names):
    """
    Normalize prices from foreign markets to USD.

    Prices from non USD currencies are converted to USD.
    :param file_names: (list) of absolute paths of saved market data
    :return: (list) normalized and ordered data
    """
    # sorting values: holds values to be sorted using heap queue
    hq = []

    # unique requests to the server: holds rates that we already downloaded
    downloaded_rates = {}

    for file_name in file_names:
        logger.debug("Processing: %s", file_name)
        print 'Processing: ', file_name

        marked_name, currency = io.parse_currency(file_name)

        # get exchange rate for currency
        if currency in downloaded_rates:
            exchange_rate = downloaded_rates[currency]
        else:
            exchange_rate = network.download_exchange_rates(currency)\
                if currency != constants.currency.BASE_CURRENCY\
                else 1.0
            downloaded_rates[currency] = exchange_rate

        # include and process only data with valid exchange rate
        if exchange_rate:
            normalized_data = _normalize_prices(file_name, exchange_rate)
            _preprocess_data(hq, normalized_data, marked_name)

    ordered_data_ = _get_ordered_data(hq)
    return ordered_data_
