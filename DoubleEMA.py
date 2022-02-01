from algorithm import Algorithm
from tools.graph import Graph
from tools.indicator import Indicator


class DoubleEMA(Algorithm):
    """
    Exponential Moving Average Strategy
    Capture the trend, using two EMAs(Periods of 15 & 25)
    1. Detect EMAs crossover.
    2. Detect prices to be higher than both EMAs. (pricetest)
    3. Wait until the price is tested atleast twice (2st step) (confirmation).
    4. Buy at market price if price is tested for a third time (2st step).
    5. Place a stop loss on 2 pips bellow current EMA(25)
    6. Place a take profits limit at... TODO
    7. Close position if inversed trend/crossover is detected.
    """

    # Ema Periods
    emaShortPeriod = 10
    emaLongPeriod = 25

    # Ask Market
    lastEmaShort = 0
    lastEmaLong = 0
    upTrendWindow = 0

    # Bid Market
    lastBidEmaShort = 0
    lastBidEmaLong = 0

    # Helpers
    startEquity = 0

    def start(self, firstCandle, allCandles):
        print("First Tick")
        self.startEquity = self.fxcm.getAccountInfo()['equity']

    def tick(self, newCandle, allCandles):
        if (len(allCandles) < self.emaLongPeriod):
            return
        self.detectCrossOverWindows(newCandle, allCandles)
        # Open a buy position if signal is confirmed, then reset (close) the signal window.
        if (self.isBuyConfirmed()):
            self.fxcm.buy(500, limit=4, stop=-2)
            self.upTrendWindow = 0
        # Close position if trend is bearish.
        if (len(self.fxcm.getOpenPositions('list')) == 1 and self.upTrendWindow == -1):
            pos = self.fxcm.getOpenPositions('list')[0]
            self.fxcm.closePosition(pos['tradeId'])


    def end(self, lastCandle, allCandles):
        print("Last tick")

        accountInfo = self.fxcm.getAccountInfo()
        Graph.setTitle(
            "Final Account Equity: {} : {}% / Strategy: DoubleEMA".format(accountInfo['equity'], ((accountInfo['equity'] - self.startEquity) / self.startEquity) * 100))

        Graph.addIndicator(
            x=allCandles.index.to_pydatetime(),
            y=Indicator.ema(allCandles['askclose'], self.emaShortPeriod),
            name='EMA {}'.format(self.emaShortPeriod),
            color="rgba(255, 0, 0, 0.6)"
        )

        Graph.addIndicator(
            x=allCandles.index.to_pydatetime(),
            y=Indicator.ema(allCandles['askclose'], 50),
            name='EMA {}'.format(self.emaLongPeriod),
            color="rgba(0, 0, 255, 0.6)"
        )

        Graph.addIndicator(
            x=allCandles.index.to_pydatetime(),
            y=Indicator.ema(allCandles['bidclose'], self.emaShortPeriod),
            name='EMA {}'.format(self.emaShortPeriod),
            color="rgba(255, 0, 0, 0.6)",
            plot=2
        )

        Graph.addIndicator(
            x=allCandles.index.to_pydatetime(),
            y=Indicator.ema(allCandles['bidclose'], 50),
            name='EMA {}'.format(self.emaLongPeriod),
            color="rgba(0, 0, 255, 0.6)",
            plot=2
        )

    def detectCrossOverWindows(self, lastCandle, allCandles):
        emaShort = Indicator.ema(allCandles['askclose'][-self.emaShortPeriod:], self.emaShortPeriod)[-1]
        emaLong = Indicator.ema(allCandles['askclose'][-self.emaLongPeriod:], self.emaLongPeriod)[-1]
        emaBidShort = Indicator.ema(allCandles['bidclose'][-self.emaShortPeriod:], self.emaShortPeriod)[-1]
        emaBidLong = Indicator.ema(allCandles['bidclose'][-self.emaLongPeriod:], self.emaLongPeriod)[-1]
        if (self.lastEmaLong == 0 or self.lastBidEmaLong == 0):
            self.lastEmaShort = emaShort
            self.lastEmaLong = emaLong
            self.lastBidEmaShort = emaBidShort
            self.lastBidEmaLong = emaBidLong
            return
        crossedUp = (self.lastEmaShort <
                     self.lastEmaLong and emaShort > emaLong)
        crossedDown = (self.lastBidEmaShort >
                       self.lastBidEmaLong and emaBidShort < emaBidLong)
        distance = (lastCandle['askclose'] - emaShort) * 100000
        if (crossedUp):
            self.upTrendWindow = 1
            Graph.addAction(
                lastCandle.name,
                emaShort,
                'Crossed UP - {}'.format(distance),
                None, 1)
        if (crossedDown):
            self.upTrendWindow = -1
            # Sell if crossing is bearish.
            if (len(self.fxcm.getOpenPositions('list')) > 0):
                pos = self.fxcm.getOpenPositions('list')[0]
                self.fxcm.closePosition(pos['tradeId'])
            Graph.addAction(
                lastCandle.name,
                emaBidShort,
                'Crossed Down',
                None, 2)

        if (self.upTrendWindow > 0 and emaShort <= lastCandle['askclose'] and emaLong <= lastCandle['askclose']):
            self.upTrendWindow += 1

        # Reset if price is lower than the emaLong. (Detect changing trend)
        if (emaLong > lastCandle['askclose']):
            self.upTrendWindow = 0

        # Reset if trend window was opened, but difference between indicators is not strong for confirmation
        distance = (lastCandle['askclose'] - emaShort) * 100000
        if (self.upTrendWindow > 0 and distance < 12):
            self.upTrendWindow = 0
            Graph.addAction(
                lastCandle.name,
                lastCandle['askclose'],
                'Ignored Trend - {}'.format(distance),
                None, 1)
        self.lastEmaShort = emaShort
        self.lastEmaLong = emaLong
        self.lastBidEmaShort = emaBidShort
        self.lastBidEmaLong = emaBidLong

    def isBuyConfirmed(self):
        return (self.upTrendWindow > 1)
