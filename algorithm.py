from tools.graph import Graph
from tools.indicator import Indicator
from datetime import datetime
from time import sleep
import pandas as pd


class Algorithm():
    fxcm = None
    config = None

    def __init__(self, fxcm, config):
        self.fxcm = fxcm
        self.config = config

    def nextTick(self, nextCandle, allCandles):
        if self.isFirstTick(allCandles):
            self.firstTick(nextCandle, allCandles)
        elif self.isLastTick(nextCandle):
            self.lastTick(nextCandle, allCandles)
        else:
            self.tick(nextCandle, allCandles)

    def isFirstTick(self, allCandles):
        return len(allCandles) == 1

    def firstTick(self, firstCandle, allCandles):
        self.start(firstCandle, allCandles)

    def isLastTick(self, nextCandle):
        return nextCandle.empty

    def lastTick(self, lastCandle, allCandles):
        self.fxcm.closePositions()
        self.end(lastCandle, allCandles)

        Graph.addCandleSticks(
            x=allCandles.index.to_pydatetime(),
            open=allCandles['askopen'],
            high=allCandles['askhigh'],
            low=allCandles['asklow'],
            close=allCandles['askclose'],
            name='Ask Candles ')

        Graph.addCandleSticks(
            x=allCandles.index.to_pydatetime(),
            open=allCandles['bidopen'],
            high=allCandles['bidhigh'],
            low=allCandles['bidlow'],
            close=allCandles['bidclose'],
            name='Bid Candles ',
            plot=2)
        Graph.render()

    def getUpperPeriod(self, periodCandles, period, nextCandle, allCandles):
        if periodCandles.empty == True:
            periodCandles = periodCandles.append(nextCandle)
        elif (nextCandle.name - periodCandles.iloc[-1].name).seconds / 60 >= period:
            allPeriodCandles = allCandles.iloc[-period:]
            newPeriodCandle = pd.Series({
                'bidopen': allPeriodCandles.iloc[0]['bidopen'],
                'bidlow': min(allPeriodCandles['bidlow']),
                'bidhigh': max(allPeriodCandles['bidhigh']),
                'bidclose': allPeriodCandles.iloc[-1]['bidclose'],
                'askopen': allPeriodCandles.iloc[0]['askopen'],
                'asklow': min(allPeriodCandles['asklow']),
                'askhigh': max(allPeriodCandles['askhigh']),
                'askclose': allPeriodCandles.iloc[-1]['askclose'],
                'tickqty': sum(allPeriodCandles['tickqty'])},
                name=allPeriodCandles.iloc[-1].name
            )
            periodCandles = periodCandles.append(newPeriodCandle)
        return periodCandles

    def isAnyPositionOpen(self):
        return len(self.fxcm.getOpenPositions('list')) != 0

    def start(self, firstCandle, allCandles):
        raise NotImplementedError(
            "Your algorithm should implement a start function.")

    def tick(self, nextCandle, allCandles):
        raise NotImplementedError(
            "Your algorithm should implement a tick function.")

    def end(self, lastCandle, allCandles):
        raise NotImplementedError(
            "Your algorithm should implement an end function.")
