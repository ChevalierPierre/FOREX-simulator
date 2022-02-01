from algorithm import Algorithm
from tools.graph import Graph
from tools.indicator import Indicator


class BBStrategy(Algorithm):
    BB_PERIOD = 25
    BB_SQUEEZE_MAX_DURATION = 50
    BB_SQUEEZE_WIDTH = dict({'m1': 0.0006, 'm5': 0.001})

    # m5Candles = None

    bbTrending = 'no'
    bbSqueezing = None
    bbSqueezeWidth = None
    bbSqueezeDuration = 0

    def start(self, firstCandle, allCandles):
        self.bbSqueezeWidth = self.BB_SQUEEZE_WIDTH[self.config['period']]

    def tick(self, nextCandle, allCandles):
        if allCandles.shape[0] < self.BB_PERIOD:
            return

        askBbCandles = allCandles['askclose'][-self.BB_PERIOD:]
        bidBbCandles = allCandles['bidclose'][-self.BB_PERIOD:]
        bb = dict({'askbb': Indicator.bb(askBbCandles, self.BB_PERIOD),
                   'bidbb': Indicator.bb(bidBbCandles, self.BB_PERIOD)})

        lastBbSqueezing = self.bbSqueezing
        bbWidth = bb['askbb']['up'][-1] - bb['askbb']['low'][-1]
        self.bbSqueezing = bbWidth <= self.bbSqueezeWidth

        if self.bbSqueezing == True and lastBbSqueezing == True: # Add duration to bb Squeeze
            self.bbSqueezeDuration += 1
        elif self.bbSqueezing == False and lastBbSqueezing == True: # Break duration of bb Squeeze
            self.bbSqueezeDuration = 0

        if self.bbTrending != 'no':  # If trending, Look for end of trending
            if (self.bbTrending == 'down' and self.isPriceAboveBbMid(nextCandle['askclose'], bb['askbb']['mid'])) or \
                    (self.bbTrending == 'up' and self.isPriceUnderBbMid(nextCandle['askclose'], bb['askbb']['mid'])):
                self.bbTrending = 'no'
                Graph.addAction(
                    nextCandle.name, bb['askbb']['mid'][-1], 'TREENDLESS', False, 1)
                Graph.addAction(
                    nextCandle.name, bb['bidbb']['mid'][-1], 'TREENDLESS', False, 2)
        else:  # If not trending
            if self.isAnyPositionOpen():  # Look for closing position
                position = self.fxcm.getOpenPositions('list')[0]
                if (position['isBuy'] and self.isPriceAboveBbMid(nextCandle['askclose'], bb['askbb']['mid'])) or \
                        (not position['isBuy'] and self.isPriceUnderBbMid(nextCandle['bidclose'], bb['bidbb']['mid'])):
                    self.fxcm.closePosition(position['tradeId'])
            else:
                if self.isPriceAboveBbUp(nextCandle['askclose'], bb['askbb']['up']):
                    # If squeezing and squeeze duration not too long
                    if self.bbSqueezing == True and self.bbSqueezeDuration <= self.BB_SQUEEZE_MAX_DURATION:
                        self.bbTrending = 'up'
                        print("TREND UP")
                        Graph.addAction(
                            nextCandle.name, bb['askbb']['mid'][-1], 'TRENDING UP', True, 1)
                        Graph.addAction(
                            nextCandle.name, bb['bidbb']['mid'][-1], 'TRENDING UP', True, 2)
                    else:
                        print("SELL")
                        stopLimit = self.getStop(
                            bb['askbb']['up'][-1], bb['askbb']['low'][-1])
                        self.fxcm.sell(self.getMaxAmount(
                        ), stop=-stopLimit, limit=stopLimit)
                elif self.isPriceUnderBbLow(nextCandle['bidclose'], bb['bidbb']['low']):
                    # If squeezing and squeeze duration not too long
                    if self.bbSqueezing == True and self.bbSqueezeDuration <= self.BB_SQUEEZE_MAX_DURATION:
                        self.bbTrending = 'down'
                        print("TREND DOWN")
                        Graph.addAction(
                            nextCandle.name, bb['askbb']['mid'][-1], 'TRENDING DOWN', True, 1)
                        Graph.addAction(
                            nextCandle.name, bb['bidbb']['mid'][-1], 'TRENDING DOWN', True, 2)
                    else:
                        print("BUY")
                        stopLimit = self.getStop(
                            bb['bidbb']['up'][-1], bb['bidbb']['low'][-1])
                        self.fxcm.buy(self.getMaxAmount(
                        ), stop=-stopLimit, limit=stopLimit)

    def getStop(self, bbup, bblow):
        return (bbup - bblow) * 10000

    def getMaxAmount(self):
        return int(self.fxcm.getAccountInfo()['usableMargin'] / 33.3)

    def getBbWidth(self, bb):
        return list(map(lambda tuple: tuple[0] - tuple[1], list(zip(bb['up'], bb['low']))))

    def getBbTrending(self, bb, nextCandle):
        newBbTrending = self.isTrending(bb['askbb'])
        if self.bbTrending == None or self.bbTrending != newBbTrending:
            print("TREND CHANGE")
            self.bbTrending = newBbTrending
            Graph.addAction(
                nextCandle.name, bb['askbb']['mid'][-1], 0, 'TRENDING' if newBbTrending else 'TRENDLESS', True if newBbTrending else False, 1)
            Graph.addAction(
                nextCandle.name, bb['bidbb']['mid'][-1], 0, 'TRENDING' if newBbTrending else 'TRENDLESS', True if newBbTrending else False, 2)

    def isPriceAboveBbUp(self, price, bbUp):
        return price >= bbUp[-1]

    def isPriceUnderBbLow(self, price, bblow):
        return price <= bblow[-1]

    def isPriceUnderBbMid(self, price, bbMid):
        return price <= bbMid[-1]

    def isPriceAboveBbMid(self, price, bbMid):
        return price >= bbMid[-1]

    def isTrending(self, bb):
        return bb['up'][-1] - bb['low'][-1] > self.BB_M1_TRENDING

    def end(self, lastCandle, allCandles):
        accountInfo = self.fxcm.getAccountInfo()
        Graph.setTitle(
            "Final Account Equity: {} / BBStrategy".format(accountInfo['equity']))

        askbb = Indicator.bb(allCandles['askclose'], self.BB_PERIOD)
        Graph.addIndicator(
            x=allCandles.index.to_pydatetime(),
            y=askbb['up'],
            name='Ask BBup ',
            color="rgba(0, 0, 255, 0.6)"
        )

        Graph.addIndicator(
            x=allCandles.index.to_pydatetime(),
            y=askbb['mid'],
            name='Ask BBmid',
            color="rgba(0, 0, 200, 0.5)"
        )

        Graph.addIndicator(
            x=allCandles.index.to_pydatetime(),
            y=askbb['low'],
            name='Ask BBlow',
            color="rgba(0, 0, 180, 0.4)"
        )

        bidbb = Indicator.bb(allCandles['bidclose'], self.BB_PERIOD)
        Graph.addIndicator(
            x=allCandles.index.to_pydatetime(),
            y=bidbb['up'],
            name='Bid BBup ',
            color="rgba(0, 0, 255, 0.6)",
            plot=2
        )

        Graph.addIndicator(
            x=allCandles.index.to_pydatetime(),
            y=bidbb['mid'],
            name='Bid BBmid',
            color="rgba(0, 0, 200, 0.5)",
            plot=2
        )

        Graph.addIndicator(
            x=allCandles.index.to_pydatetime(),
            y=bidbb['low'],
            name='Bid BBlow',
            color="rgba(0, 0, 180, 0.4)",
            plot=2
        )

        # bidbbWidth = self.getBbWidth(bidbb)
        # Graph.addIndicator(
        #     x=allCandles.index.to_pydatetime(),
        #     y=bidbbWidth,
        #     name='Bid BB width',
        #     color="rgba(0, 0, 180, 0.4)",
        #     plot=3
        # )

        # askbbWidth = self.getBbWidth(askbb)
        # Graph.addIndicator(
        #     x=allCandles.index.to_pydatetime(),
        #     y=askbbWidth,
        #     name='Ask BB width',
        #     color="rgba(0, 0, 180, 0.4)",
        #     plot=3
        # )
