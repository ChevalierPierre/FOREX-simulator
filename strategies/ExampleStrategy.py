from algorithm import Algorithm
from tools.graph import Graph
from tools.indicator import Indicator


class ExampleStrategy(Algorithm):
    def start(self, firstCandle, allCandles):
        print("First Tick")

    def tick(self, newCandle, allCandles):
        print("Tick TOTO rdtfyguhijok")

    def end(self, lastCandle, allCandles):
        print("Last tick")
        accountInfo = self.fxcm.getAccountInfo()
        Graph.setTitle(
            "Final Account Equity: {} / ExampleStrategy".format(accountInfo['equity']))

        Graph.addIndicator(
            x=allCandles.index.to_pydatetime(),
            y=Indicator.ema(allCandles['askclose'], 20),
            name='EMA 20',
            color="rgba(0, 255, 0, 0.6)"
        )
