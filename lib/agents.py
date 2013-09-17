# -*- coding: utf-8 -*-

"""
Functions to simulate agent behaviour.
"""

import bisect
import logging
import sys
import lib.io as io
import lib.statistics as stat

logger = logging.getLogger(__name__)
#average market transaction fee
FEE = 0.0065


def _getBuyCriteria1(_trade_price, _future_trade_price, _traded_amount, _bought):
    """
    Decides when an agent in the market has bought the financial instrument.

    Every trade transfers the financial instrument from one agent to another. Here we accumulate what every agent has
    bought and at what time the event occurred.
    :param _trade_price: (float) price of the trade
    :param _future_trade_price: (float) price of the future trade
    :param _traded_amount: (float) amount traded
    :param _bought: (list) container holding all buying events: [(_trade_price, _traded_amount)]
    :return: Nothing. Side effects: _bought is changed
    """
    try:
        logger.info('getBuyCriteria: Evaluating action: buy')

        #if a trade occurred there was a transfer of the instrument between agents
        if _trade_price <= _future_trade_price:
            #insert sorted
            bisect.insort(_bought, (_trade_price, _traded_amount))

    except:
        raise


def _getNegPotentialVol(_trade_price, _greed, _bought):
    """
    Estimate the financial instrument's volume of all the agents that are willing to sell.

    If the estimated amount is greater than some experimental constant, the price is likely to fall.
    :param _trade_price: (float) current trade price
    :param _greed: (float) agent's simulated greed
    :param _bought: (list) container holding all buying events: [(_trade_price, _traded_amount)]
    :return: (float) forecasted volume for action sell
    """
    try:
        logger.info('getNegPotentialVol: Forecasting energy flow.')

        #cumulative volume that will potentially be sold as a result of new signal
        forecasted_sold_volume = 0

        #check response of all that already bought to the new signal - signal change
        for tpl in _bought:
            bought_price = tpl[0]
            bought_amount = tpl[1]

            #agent wants at least _greed percent profit
            margin = bought_price * _greed
            #calculate the costs of the trade
            fee = _trade_price * FEE + bought_price * FEE
            anticipated_target = bought_price + margin + fee
            logger.debug('getNegPotentialVol: anticipated_target: %s' % anticipated_target)

            #estimate profitable amount at current price
            #if we already achieved desired profit, the agent will sell now
            if anticipated_target <= _trade_price:
                #all the profitable volume at this signal
                forecasted_sold_volume += bought_amount

            #if selling is not profitable, the agent should hold
            else:
                break

        return forecasted_sold_volume

    except:
        raise


def _updateSysVol(_vol_cumulative, _bought):
    """
    Updates the system energy.

    Energy is flowing from and into the system. Here we're updating the system at maximum resolution.
    :param _vol_cumulative: (float) amount traded
    :param _bought: (list) container holding all buying events: [(_trade_price, _traded_amount)]
    :return: Nothing. Side effects: _bought is changed.
    """
    try:
        logger.info('updateSysVol: Updating system.')

        #starting value, should be !=0 to start the loop!
        leftover = 1

        while leftover != 0:
            if len(_bought):
                smallest_item = _bought[0]
                bought_price = smallest_item[0]
                bought_volume = smallest_item[1]

                #get most profitable investment at current price
                leftover = bought_volume - _vol_cumulative
                logger.debug('updateSysVol: Most profitable investment: %s' % leftover)

                #remove investments with zero amount
                if leftover == 0:
                    del _bought[0]

                #change volume of the most profitable investment
                elif leftover > 0:
                    _bought[0] = (bought_price, leftover)
                    leftover = 0

                #handle the rest
                elif leftover < 0:
                    _vol_cumulative -= bought_volume
                    del _bought[0]

                    #That would be true if all the created E originated from this system. But it's created also out of
                    # the system! E.g. mining - obtaining items without putting any energy in the system, obtaining
                    # items by putting energy in outer systems and transferring it to ours.
                    #Check that energy out of the system is not greater than energy already in the system! Note that
                    #  we're checking for _vol_cumulative and not _traded_amount so for _vol_cumulative this shouldn't
                    #  happen!
                    if len(_bought) == 0:
                        #account for numerical errors like "Left E: 4.234e-13"
                        if (_vol_cumulative - 0.001) > 0:
                            logger.error('Energy left: %s' % _vol_cumulative)
                            raise AssertionError

            #we processed everything
            else:
                break

    except AssertionError:
        logger.error('There is still energy to be pulled out of the system but there are no more candidates!')
        sys.exit()

    except:
        raise


def _getSellCriteria(_trade_price, _future_trade_price, _traded_amount, _bought, _greed):
    """
    Decides when an agent in the market has sold the financial instrument.


    We're interested in the cumulative profitable volume at some signal: Buyers buy a bag of things and only in 70% of
     all cases (based on simulations) they sell all at once. When they sell only parts, our prediction suffers. Note
     that predicting when the agent will pull energy out of the sys is a matter of G(Ai).
    :param _trade_price: (float) price of the trade
    :param _future_trade_price: (float) price of the future trade
    :param _traded_amount: (float) amount traded
    :param _bought: (list) container holding all buying events: [(_trade_price, _traded_amount)]
    :param _greed: (float) simulated agent's greed
    :return: Nothing. Side effects: _bought is changed
    """
    try:
        logger.info('getSellCriteria: Evaluating action: sell')

        forecasted_sell_volume = _getNegPotentialVol(_trade_price, _greed, _bought)
        logger.debug('getSellCriteria: Forecasted_sell_volume: %s' % forecasted_sell_volume)

        number_of_buy_events = len(_bought)

        #extract sample data for later interactive analysis
        if number_of_buy_events >= 4:
            bought_price0 = _bought[0][0]
            bought_vol0 = _bought[0][1]
            bought_price1 = _bought[1][0]
            bought_vol1 = _bought[1][1]
            bought_price2 = _bought[2][0]
            bought_vol2 = _bought[2][1]
            bought_price3 = _bought[3][0]
            bought_vol3 = _bought[3][1]

            margin0 = float(_trade_price) / float(bought_price0)
            margin1 = float(_trade_price) / float(bought_price1)
            margin2 = float(_trade_price) / float(bought_price2)
            margin3 = float(_trade_price) / float(bought_price3)

        else:
            bought_vol0 = bought_vol1 = bought_vol2 = bought_vol3 = 0
            margin0 = margin1 = margin2 = margin3 = 0

        #if energy pulled from the system update available volume and get vol_from_outer_sys
        vol_from_outer_sys = 0

        #For energy in flow we already know the only possible way is for energy to come from outside. Here we're only
        #  interested in the energy's out flow.
        if _trade_price > _future_trade_price:
            #check how much energy came from outer systems
            vol_from_outer_sys = _traded_amount - forecasted_sell_volume

            #energy out < than forecasted_sell_volume, which is OK
            if vol_from_outer_sys < 0:
                #since we're not interested in energy from outer systems
                vol_from_outer_sys = -1
                _updateSysVol(_traded_amount, _bought)

        return {
            'forecasted_sell_volume': forecasted_sell_volume,
            'number_of_buy_events': number_of_buy_events,
            'margin0': margin0,
            'margin1': margin1,
            'margin2': margin2,
            'margin3': margin3,
            'margin0_volume': bought_vol0,
            'margin1_volume': bought_vol1,
            'margin2_volume': bought_vol2,
            'margin3_volume': bought_vol3,
            'vol_from_outer_sys': vol_from_outer_sys,
        }

    except:
        raise


#check how accurate can you predict agent's actions
def _getModelAccuracy(_current_response,
                      _trade_price,
                      _future_trade_price,
                      _forecasted_sell_volume,
                      _previous_price,
                      _track_accuracy):
    """
    Estimates how accurate the model prediction is.

    :param _current_response: (list) current agent responses
    :param _trade_price: (float) current trade price
    :param _future_trade_price: (float) next nearest future price
    :param _forecasted_sell_volume: (float) simulated volume to be sold
    :param _previous_price: (list) previous response from agents
    :param _track_accuracy: (map) tracks model statistics
    :return: (dict) merged statistics: {'local_statistics': {}, 'global_statistics': {}}
    """
    try:
        logger.info('getModelAccuracy: Calculating model statistics.')

        global_statistics = stat.getGlobalStatistics(
            _trade_price,
            _future_trade_price,
            _forecasted_sell_volume,
            _previous_price,
            _track_accuracy
        )

        local_statistics = stat.getLocalStatistics(_current_response)

        #return merged statistics
        return dict(global_statistics.items() + local_statistics.items())

    except:
        raise


def getAgentReactions(_simulation_data, _greed):
    """
    Simulate how agents react to price changes.

    :param _simulation_data: (list) market data: [unix time, trade price, trade amount]
    :param _greed: (float) simulated agent's greed
    :return: (list) simulated responses
    """
    try:
        logger.info('getAgentReactions: Simulating agent reaction')

        #for measuring progress we need to know how much is there still to process
        size_to_process = len(_simulation_data)

        #index for measuring relative progress of execution
        progress = 0

        #simulate buying: holds events when agent bought the financial instrument
        bought = []

        #simulate response: holds agent responses
        current_response_ = []
        #simulate response: past price
        previous_price = 0

        #track model accuracy: holds metrics for evaluating model accuracy
        track_accuracy = {'true_positive': 0, 'true_negative': 0, 'false_positive': 0, 'false_negative': 0}

        for index in xrange(len(_simulation_data) - 1):
            current_data_chunk = _simulation_data[index]
            trade_price = current_data_chunk[1]
            trade_amount = current_data_chunk[2]

            next_data_chunk = _simulation_data[index + 1]
            future_trade_price = next_data_chunk[1]

            #simulate agent's buying decisions
            _getBuyCriteria1(trade_price, future_trade_price, trade_amount, bought)

            #simulate agent's selling decisions
            forecasted_data = _getSellCriteria(trade_price, future_trade_price, trade_amount,
                                               bought, _greed)

            #check how relevant is the model
            if current_response_:
                previous_price = current_response_[index - 1]['trade_price']

            accuracy = _getModelAccuracy(
                current_response_,
                trade_price,
                future_trade_price,
                forecasted_data['forecasted_sell_volume'],
                previous_price,
                track_accuracy
            )

            current_response_.append(
                {
                    'trade_price': trade_price,
                    'forecast': forecasted_data,
                    'statistics': accuracy
                }
            )

            #print progress to console
            progress += 1
            io.displayProgress(progress, size_to_process, accuracy)

        return current_response_

    except:
        raise