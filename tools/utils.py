import configparser
import pandas as pd
import tools.const as const


def displayDataFrame(dataFrame):
    """Display a panda's dataFrame object.

    Args:
        dataFrame (dataFrame): dataFrame object to display
    """
    pd.set_option('display.max_rows', dataFrame.shape[0] + 1)
    pd.set_option('display.max_columns', dataFrame.shape[1] + 1)
    print(dataFrame)
    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')


def isDiffCandle(candle1, candle2):
    return candle1.name == candle2.name


def getOpenPrice(isBuy, lastCandle):
    return lastCandle['askclose'] if isBuy else lastCandle['bidclose']


def getClosePrice(isBuy, lastCandle):
    return lastCandle['bidclose'] if isBuy else lastCandle['askclose']


def getPL(isBuy, amount, openPrice, closePrice):
    return (closePrice - openPrice if isBuy else openPrice - closePrice) * amount * const.LOT_SIZE


def getSpread(lastCandle):
    return lastCandle['askclose'] - lastCandle['bidclose']


def getLimit(isBuy, limit, openPrice):
    limit /= const.LOT_SIZE
    return openPrice + limit if isBuy else openPrice - limit


def getStop(isBuy, stop, openPrice, spread):
    stop /= const.LOT_SIZE
    return openPrice + stop - spread if isBuy else openPrice - stop + spread


def getPipCost(forexPair, date, con):
    if forexPair.find('JPY') == -1:
        multiplier = 0.0001
    else:
        multiplier = 0.01

    forexPairExchange = con.get_candles(
        forexPair, period='m1', number=1, start=date, end=date, columns=["askopen"])
    if forexPairExchange.size == 0:
        return getPipCost(forexPair, date - dt.timedelta(minutes=1))
    forexPairExchangeValue = forexPairExchange['askopen'].iloc[0]
    if forexPair.find(const.ACCOUNT_CURRENCY) != -1:
        return multiplier / forexPairExchangeValue * (const.LOT_SIZE / 10)
    else:
        forexPairSecond = forexPair.split('/')[1]
        return getPipCost(const.ACCOUNT_CURRENCY + '/' + forexPairSecond)


def checkLimitStopViability(limit, stop):
    if limit and limit < 0:
        return False
    if stop and stop > 0:
        return False
    return True


def checkLimitStop(isBuy, limit, stop, closePrice):
    if limit != 0:
        if isBuy and limit <= closePrice:
            return True
        elif not isBuy and limit >= closePrice:
            return True
    if stop != 0:
        if isBuy and stop >= closePrice:
            return True
        elif not isBuy and stop <= closePrice:
            return True
    return False


def parseConfigFile(argv):
    config = configparser.ConfigParser()
    try:
        config.read(argv[1])
        if not 'FXCM_BOT' in config or not 'backtest' in config['FXCM_BOT']:
            raise Exception("Missing FXCM_BOT section or backtest field")
        if not 'end_date' in config['FXCM_BOT'] or (config['FXCM_BOT']['backtest'] == 'true' and not 'start_date' in config['FXCM_BOT']):
            raise Exception("Missing start_date or end_date fields")
        return dict(config['FXCM_BOT'])
    except Exception as error:
        print("Error while parsing config file '%s': %s" % (argv[1], error))
        return None
