import sys
import pandas as pd

def ptdrCFermeLeWeekend():
    data = pd.read_csv("config/exampleData_EURUSD.csv")

    data['askopen'] = data['bidopen'].map(lambda x: x + 0.00013)
    data['asklow'] = data['bidlow'].map(lambda x: x + 0.00013)
    data['askhigh'] = data['bidhigh'].map(lambda x: x + 0.00013)
    data['askclose'] = data['bidclose'].map(lambda x: x + 0.00013)
    datetime_series = pd.to_datetime(data['date'])
    datetime_index = pd.DatetimeIndex(datetime_series.values)
    data = data.drop('date', 'columns')
    return data.set_index(datetime_index)