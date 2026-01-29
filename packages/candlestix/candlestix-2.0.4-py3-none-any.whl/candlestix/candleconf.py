from enum import Enum


class Candle:

    def __init__(self, length_in_minutes: int, api_length_val: str, days_to_fetch):
        self.__length_in_minutes = length_in_minutes
        self.__api_length_val = api_length_val
        self.__days_to_fetch = days_to_fetch

    def get_length_in_minutes(self):
        return self.__length_in_minutes

    def get_api_length_val(self):
        return self.__api_length_val

    def get_days_to_fetch(self):
        return self.__days_to_fetch


class CandleLength(Enum):
    """
    Upstox supports only the following candle lengths:

    For current day:
        - 1 minute
        - 30 minutes

    For all past days except today:
        - 1 minute (only for last 6 months from end-date)
        - 30 minutes (only for last 6 months from end-date)
        - 1 day (only for 1 year from end-date)
        - 1 week (only for 10 years from end-date)
        - 1 month (only for 10 years from end-date)

    Note: For basis of 'days_to_fetch' refer to excel sheet in docs folder.
    """

    ONE_MIN = Candle(1, '1minute', 5)       # 1875 data points
    FIVE_MIN = Candle(5, '1minute', 6)      # 450 data points
    TEN_MIN = Candle(10, '1minute', 10)     # 375 data points
    FIFTEEN_MIN = Candle(15, '1minute', 16) # 400 data points
    THIRTY_MIN = Candle(30, '30minute', 32) # 400 data points
    ONE_HOUR = Candle(60, '30minute', 64)   # 400 data points
    DAY = Candle(24 * 60, 'day', 730)                      # 730 data points
    WEEK = Candle(7 * 24 * 60, 'week', 0)  # upstox standard
    MONTH = Candle(30 * 7 * 24 * 60, 'month', 0)  # upstox standard

    @staticmethod
    def from_name_str(s):
        return CandleLength.__members__.get(s)


class Exchange(Enum):
    BSE = "BSE_EQ"
    NSE = 'NSE_EQ'
    NSE_INDEX = 'NSE_INDEX'
    BSE_INDEX = 'BSE_INDEX'
    OPTIDX = 'OPTIDX'
    OPTSTK = 'OPTSTK'


class Constants:
    API_VERSION = '2.0'
    API_STATUS_ERROR = "error"
    API_STATUS_SUCCESS = "success"


if __name__ == '__main__':
    x = CandleLength.from_name_str('ONE_MIN')
    assert x == CandleLength.ONE_MIN
    print(x)

    x = CandleLength.from_name_str('MONTH')
    assert x == CandleLength.MONTH
    print(x)

    x = CandleLength.from_name_str('Z')
    assert x is None
    print(x)

    x = CandleLength.from_name_str(None)
    assert x is None
    print(x)
