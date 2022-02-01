# import fxcmpy
from tools.graph import Graph
from tools.convertisseur import ptdrCFermeLeWeekend
import signal
from time import sleep
import datetime as dt
import pandas as pd
import tools.utils as utils
import tools.const as const


class FxcmBacktest():

    __con = None

    __forexPair = 'EUR/USD'
    __config = None

    __account = dict({
        'balance': const.START_AMOUNT,
        'equity': const.START_AMOUNT,
        'usableMargin': const.START_AMOUNT,
        'usdMr': 0,
        'grossPL': 0
    })
    __leftCandles = None
    __candles = None

    __openPositions = list()
    __closePositions = list()

    def __init__(self, config, con):
        if config['devEnv'] == False:
            # self.__con = fxcmpy.fxcmpy(config_file='config/fxcm.cfg')
            self.__con = None
        else:
            self.__con = con

        startDate = dt.datetime.strptime(
            config['start_date'], "%Y/%m/%d %H:%M")
        endDate = dt.datetime.strptime(
            config['end_date'], "%Y/%m/%d %H:%M")

        self.__config = config
        self.__leftCandles = self.getCandles(
            config['period'], start=startDate, end=endDate)
        self.__candles = pd.DataFrame(columns=self.__leftCandles.columns)

        # End bot when Trigger Crtl-C
        signal.signal(signal.SIGINT, self.__end)

    def getAccountInfo(self):
        return self.__account

    def setForexPair(self, newForexPair):
        """Set a new pair of Forex to work with

        Args:
            newForexPair (str): New pair of Forex
        """
        self.__forexPair = newForexPair

    def getForexPair(self):
        """Get the actual pair of Forex

        Returns:
            str: Actual pair of Forex
        """
        return self.__forexPair

    def getCandles(self, period, number=10, start=None, end=None, columns=[]):
        """Return historical market data from the fxcm database

        Args:
            period (str): Granularity of the data. Possible values are: ‘m1’, ‘m5’, ‘m15’, ‘m30’, ‘H1’, ‘H2’, ‘H3’, ‘H4’, ‘H6’, ‘H8’, ‘D1’, ‘W1’, or ‘M1’.
            number (int, optional): Number of candles to receive. Defaults to 10.
            start (datetime, optional): First date to receive data for. Defaults to None.
            end (datetime, optional): Last date to receive data for. Defaults to None.
            columns (list, optional): List of column labels the result should include. If empty, all columns are returned. Possible values are: ‘date’, ‘bidopen’, ‘bidclose’, ‘bidhigh’, ‘bidlow’, ‘askopen’, ‘askclose’, ‘askhigh’, ‘asklow’, ‘tickqty’. Also available is ‘asks’ as shortcut for all ask related columns and ‘bids’ for all bid related columns, respectively. Defaults to [].

        Returns:
            DataFrame: Requested data
        """
        return self.__con.get_candles(self.__forexPair, period=period, number=number, start=start, end=end, columns=columns)

    def getNewCandle(self):
        # End bot when there is no leftover candles
        if self.__leftCandles.empty:
            return (pd.Series(), self.__candles)

        # Get nextCandle and remove nextCandle from leftover candles
        nextCandle = self.__leftCandles.iloc[0]
        self.__candles = self.__candles.append(nextCandle)
        self.__leftCandles = self.__leftCandles.iloc[1:]

        # Update all positions with new Candle
        for position in self.__openPositions:
            position.update(nextCandle)
        self.__updateAccountInfo()

        return (nextCandle, self.__candles)

    def buy(self, amount, limit=None, stop=None):
        return self.__openPosition(True, amount, limit, stop)

    def sell(self, amount, limit=None, stop=None):
        return self.__openPosition(False, amount, limit, stop)

    def getOpenPositions(self, kind="dataframe"):
        """Get all opened positions

        Args:
            kind (str, optional): How to return the data. Possible values are: 'dataframe' or 'list'. Defaults to "dataframe"".
        """
        positionsList = [position.get_position()
                         for position in self.__openPositions]
        if kind == 'dataframe':
            return pd.DataFrame(data=positionsList)
        return positionsList

    def getOpenPosition(self, positionId):
        """Get an opened position by his Id

        Args:
            positionId (int): Id of the position
        """
        return next(position for position in self.__openPositions if position.get_tradeId() == positionId)

    def getClosePositions(self, kind="dataframe"):
        """Get all closed positions

        Args:
            kind (str, optional): How to return the data. Possible values are: 'dataframe' or 'list'. Defaults to "dataframe"".
        """
        positionsList = [position.get_position()
                         for position in self.__closePositions]
        if kind == 'dataframe':
            return pd.DataFrame(data=positionsList)
        return positionsList

    def getClosePosition(self, positionId):
        """Get a closed position by his Id

        Args:
            positionId (int): Id of the position
        """
        return next(position for position in self.__closePositions if position.get_tradeId() == positionId)

    def closePositions(self):
        for position in self.__openPositions:
            self.closePosition(position.get_tradeId())

    def closePosition(self, positionId):
        """Close a position by his Id

        Args:
            positionId (int): Id of the position
        """
        position = self.getOpenPosition(positionId)
        self.__account['balance'] += position.get_grossPL()
        self.__account['usdMr'] -= position.get_usedMargin()
        self.__openPositions.remove(position)
        self.__closePositions.append(FxcmBacktestClosePosition(position))
        self.__updateAccountInfo()
        isBuy = position.get_isBuy()
        Graph.addAction(self.__getLastCandle().name, position.get_close(
        ), 'Close #' + str(positionId) + ' (' + str(round(position.get_grossPL(), 2)) + ')', isBuy, 2 if isBuy else 1)
        return True

    def getCon(self):
        return self.__con

    def __end(self, sig, frame):
        print("\nEnding Bot...")
        self.__leftCandles = self.__leftCandles[0:0]

    def __updateAccountInfo(self):
        newGrossPL = sum([position.get_grossPL()
                          for position in self.__openPositions])

        self.__account['grossPL'] = newGrossPL
        self.__account['equity'] = self.__account['balance'] + newGrossPL
        self.__account['usableMargin'] = self.__account['equity'] - \
            self.__account['usdMr']

    def __openPosition(self, isBuy, amount, limit, stop):
        lastCandle = self.__getLastCandle()

        if not utils.checkLimitStopViability(limit, stop):
            print("ERROR: Can't open position: Limit or Stop value is incorrect")
            return None

        newTradeId = len(self.__openPositions) + len(self.__closePositions)
        newPosition = FxcmBacktestOpenPosition(
            self, lastCandle, newTradeId, self.__forexPair, isBuy, amount, limit, stop)

        if self.__account['usableMargin'] - (newPosition.get_usedMargin() * amount * 2) < 0:
            print("ERROR: Can't open position: Not enough usable margin.")
            return None
        self.__account['usdMr'] += newPosition.get_usedMargin()

        Graph.addAction(lastCandle.name, newPosition.get_open(),
                        'Open #' + str(newTradeId), isBuy, 1 if isBuy else 2)
        self.__openPositions.append(newPosition)
        return newPosition.get_tradeId()

    def __getLastCandle(self):
        if len(self.__candles) == 0:
            return self.__leftCandles.iloc[0]
        return self.__candles.iloc[-1]


class FxcmBacktestOpenPosition():
    __fxcm = None
    __position = None

    def __init__(self, fxcm, lastCandle, tradeId, forexPair, isBuy, amount, limit, stop):
        self.__fxcm = fxcm

        self.__position = pd.Series({
            'tradeId': tradeId,
            'currency': forexPair,
            'currencyPoint': utils.getPipCost(forexPair, lastCandle.name, self.__fxcm.getCon()),
            'isBuy': isBuy,
            'amountK': amount,
            'time': lastCandle.name,
            'limit': 0,
            'stop': 0,
            'open': utils.getOpenPrice(isBuy, lastCandle),
            'close': 0,
            'grossPL': 0,
            'visiblePL': 0,
            # I don't know how to compute MMR (16.65 is commonly used but not always)
            'usedMargin': const.MMR
        })

        # Define limit and stop value from pips
        self.__position['limit'] = utils.getLimit(
            isBuy, limit, self.__position['open']) if limit else 0
        self.__position['stop'] = utils.getStop(
            isBuy, stop, self.__position['open'], utils.getSpread(lastCandle)) if stop else 0

        self.__updatePrices(lastCandle)

    def update(self, lastCandle):
        self.__updatePrices(lastCandle)

        # Check limit and stop loss
        if utils.checkLimitStop(self.__position['isBuy'], self.__position['limit'], self.__position['stop'], self.__position['close']):
            self.__fxcm.closePosition(self.__position['tradeId'])

    def __updatePrices(self, lastCandle):
        # Update Position prices
        self.__position['close'] = utils.getClosePrice(
            self.__position['isBuy'], lastCandle)
        self.__position['visiblePL'] = utils.getPL(
            self.__position['isBuy'], self.__position['amountK'], self.__position['open'], self.__position['close'])
        self.__position['grossPL'] = (
            self.__position['visiblePL'] * self.__position['currencyPoint'])

    def get_position(self):
        return self.__position

    def get_tradeId(self):
        return self.__position['tradeId']

    def get_currency(self):
        return self.__position['currency']

    def get_currencyPoint(self):
        return self.__position['currencyPoint']

    def get_isBuy(self):
        return self.__position['isBuy']

    def get_amount(self):
        return self.__position['amountK']

    def get_time(self):
        return self.__position['time']

    def get_limit(self):
        return self.__position['limit']

    def get_stop(self):
        return self.__position['stop']

    def get_open(self):
        return self.__position['open']

    def get_close(self):
        return self.__position['close']

    def get_grossPL(self):
        return self.__position['grossPL']

    def get_visiblePL(self):
        return self.__position['visiblePL']

    def get_usedMargin(self):
        return self.__position['usedMargin']


class FxcmBacktestClosePosition():
    __position = None

    def __init__(self, openPosition):
        self.__position = pd.Series({
            'tradeId': openPosition.get_tradeId(),
            'currency': openPosition.get_currency(),
            'currencyPoint': openPosition.get_currencyPoint(),
            'isBuy': openPosition.get_isBuy(),
            'amountK': openPosition.get_amount(),
            'open': openPosition.get_open(),
            'close': openPosition.get_close(),
            'grossPL': openPosition.get_grossPL(),
            'visiblePL': openPosition.get_visiblePL(),
        })

    def get_position(self):
        return self.__position

    def get_tradeId(self):
        return self.__position['tradeId']

    def get_currency(self):
        return self.__position['currency']

    def get_currencyPoint(self):
        return self.__position['currencyPoint']

    def get_isBuy(self):
        return self.__position['isBuy']

    def get_amount(self):
        return self.__position['amountK']

    def get_open(self):
        return self.__position['open']

    def get_close(self):
        return self.__position['close']

    def get_grossPL(self):
        return self.__position['grossPL']

    def get_visiblePL(self):
        return self.__position['visiblePL']
