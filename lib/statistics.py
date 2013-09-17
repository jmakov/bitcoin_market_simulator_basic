# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)
#window size for local statistics
WINDOW_SIZE = 1000


def getGlobalStatistics(_trade_price, _future_trade_price, _forecasted_volume, _previous_price, _track_accuracy):
    """
    Calculates statistics on the whole interval.

    :param _trade_price: (float) current price
    :param _future_trade_price: (float)
    :param _forecasted_volume: (float) simulated amount of financial instrument to be sold
    :param _previous_price:
    :param _track_accuracy:
    :return: (map) global statistics
    """
    try:
        logger.info('getGlobalStatistics: Calculating global statistics.')

        #1 if prediction succesfull, -1 if prediction wrong, 0 if no info
        did_not_sell = did_sell = 0

        #updated system with _forecasted_sell_volume - energy is pulled out, no _forecasted_sell_volume left at
        # this point
        if _forecasted_volume < _previous_price:
            #TP: we predict signal stabilization or increase
            if _trade_price <= _future_trade_price:
                did_not_sell = 1

                _track_accuracy['true_positive'] += 1

            else:
                did_not_sell = -1

                _track_accuracy['false_positive'] += 1

        #energy is pulled from the system
        else:
            #TN: we predict signal drop
            if _trade_price > _future_trade_price:
                did_sell = 1

                _track_accuracy['true_negative'] += 1

            else:
                did_sell = -1

                _track_accuracy['false_negative'] += 1

        #global statistics - current prediction values for this model
        global_relative_positives = global_relative_negatives = 0

        no_pos = _track_accuracy['true_positive'] + _track_accuracy['false_positive']
        no_neg = _track_accuracy['true_negative'] + _track_accuracy['false_negative']

        #get global relative statistics
        if no_pos:
            global_relative_positives = float(_track_accuracy['true_positive']) / float(no_pos)
        if no_neg:
            global_relative_negatives = float(_track_accuracy['true_negative']) / float(no_neg)

        return {
            'global_statistics':
            {
                'predicted_energy_in': did_not_sell,
                'predicted_energy_out': did_sell,
                'global_relative_positives': global_relative_positives,
                'global_relative_negatives': global_relative_negatives,
            }
        }

    except:
        raise


def getLocalStatistics(_current_response):
    """
    Calculates statistics on an interval.

    :param _current_response: (list) holding agent responses
    :return: (map) local statistics
    """
    try:
        logger.info('getLocalStatistics: Calculating local statistics.')

        #set up temporary window size
        window_tmp = WINDOW_SIZE

        response_size = len(_current_response)
        no_pos_in_window = no_neg_in_window = 0

        local_true_positives = local_false_positives = local_true_negatives = local_false_negatives = 0


        #define starting point
        if response_size < WINDOW_SIZE:
            window_tmp = response_size

        start = response_size - 1 - window_tmp

        #get local statistics for window
        for dct in _current_response[start:]:
            predicted_energy_in = dct['statistics']['global_statistics']['predicted_energy_in']
            predicted_energy_out = dct['statistics']['global_statistics']['predicted_energy_out']

            if predicted_energy_in == 1:
                local_true_positives += 1

            elif predicted_energy_in == -1:
                local_false_positives += 1

            if predicted_energy_out == 1:
                local_true_negatives += 1

            elif predicted_energy_out == -1:
                local_false_negatives += 1

        local_no_pos = local_true_positives + local_true_positives
        local_no_neg = local_true_negatives + local_false_negatives

        if local_no_pos:
            no_pos_in_window = float(local_true_positives) / float(local_no_pos)

        if local_no_neg:
            no_neg_in_window = float(local_true_negatives) / float(local_no_neg)

        return {
            'local_statistics':
            {
                'local_relative_positives': no_pos_in_window,
                'local_relative_negatives': no_neg_in_window
            }
        }

    except:
        raise