from pyti.exponential_moving_average import exponential_moving_average as ema
from pyti.bollinger_bands import upper_bollinger_band as bbup
from pyti.bollinger_bands import middle_bollinger_band as bbmid
from pyti.bollinger_bands import lower_bollinger_band as bblow


class Indicator():

    # Example:
    # Data = [6, 7, 3, 6, 3, 9, 5]
    # Period = 2

    @staticmethod
    def ema(data, period):
        return ema(data, period)

    @staticmethod
    def bbup(data, period):
        return bbup(data, period)

    @staticmethod
    def bbmid(data, period):
        return bbmid(data, period)

    @staticmethod
    def bblow(data, period):
        return bblow(data, period)

    @staticmethod
    def bb(data, period):
        return dict({'up': Indicator.bbup(data, period), 'mid': Indicator.bbmid(data, period), 'low': Indicator.bblow(data, period)})
