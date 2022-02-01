import pandas as pd
import numpy as np

class MovingAverageCrossStrategy():
    """    
    Requires:
    bars - A DataFrame of bars for the above symbol.
    short_window - Lookback period for short moving average.
    long_window - Lookback period for long moving average."""

    def __init__(self, bars, short_window=50, long_window=200):
        self.bars = bars

        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self):
        """Returns the DataFrame of symbols containing the signals
        to go long, short or hold (1, -1 or 0)."""
        signals = pd.DataFrame(index=self.bars.index)
        signals['signal'] = 0.0

        # Create the set of short and long simple moving averages over the 
        # respective periods
        signals['short_mavg'] = self.bars.rolling(self.short_window, min_periods=1).mean()
        signals['long_mavg'] = self.bars.rolling(self.long_window, min_periods=1).mean()

        # Create a 'signal' (invested or not invested) when the short moving average crosses the long
        # moving average, but only for the period greater than the shortest moving average window
        signals['signal'][self.short_window:] = np.where(signals['short_mavg'][self.short_window:] 
            > signals['long_mavg'][self.short_window:], 1.0, 0.0)   

        # Take the difference of the signals in order to generate actual trading orders
        signals['positions'] = signals['signal'].diff()   

        return signals


"""
sample_close_data =pd.DataFrame([792.65, 802.44, 804.97, 810.1, 809.36, 809.74,
813.47, 817.09, 813.84, 808.33, 816.82, 818.1, 814.88, 808.54, 809.14,
793.75, 792.27, 777.49, 776.23, 765.78, 764.03, 777.64, 789.16, 785.8,
779.42, 777.89, 784.3, 784.15, 777.1, 784.32, 780.36, 773.55, 751.27,
771.75, 780.29, 805.59, 811.98, 802.03, 781.1, 782.19, 788.42, 805.48,
809.9, 819.56, 817.35, 822.1, 828.55, 835.74, 824.06, 821.63, 827.09,
821.49, 806.84, 804.6, 804.08, 811.77, 809.57, 814.17, 800.71, 803.08,
801.23, 802.79, 800.38, 804.06, 802.64, 810.06, 810.73, 802.65, 814.96,
815.95, 805.03, 799.78, 795.39, 797.97, 801.23, 790.46, 788.72, 798.82,
788.48, 802.84, 807.99, 808.02, 796.87, 791.4, 789.85, 791.92, 795.82,
793.22, 791.3, 793.6, 796.59, 796.95, 799.65, 802.75, 805.42, 801.19,
805.96, 807.05, 808.2, 808.49, 807.48, 805.23, 806.93, 797.25, 798.92,
800.12, 800.94, 791.34, 765.84, 761.97, 757.65, 757.52, 759.28, 754.41,
757.08, 753.41, 753.2, 735.63, 735.8, 729.48, 732.51, 727.2, 717.78,
707.26, 708.97, 704.89, 700])

mac = MovingAverageCrossStrategy(sample_close_data)
signal = mac.generate_signals()
print(signal)
"""