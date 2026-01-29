import pprint

import pandas as pd

from candlestix import Exchange
from candlestix.candle_loader import CandleDataLoader
from candlestix.candleconf import CandleLength


class SupportResistanceDetectorV2:
    def __init__(self, window=5, merge_percent=1.0):
        """
        Initialize the detector.
        :param window: Number of candles to look around for local extrema.
        :param merge_percent: Merge distance as a percentage of the level value.
        """
        self.window = window
        self.merge_percent = merge_percent
        self.levels = []  # Each level: {'price': float, 'timestamp': pd.Timestamp, 'count': int, 'type': 'support'/'resistance'}

    def _is_close(self, a, b):
        return abs(a - b) / b * 100 <= self.merge_percent

    def _merge_or_add_level(self, timestamp, price, level_type):
        for level in self.levels:
            if self._is_close(price, level['price']):
                level['count'] += 1
                level['timestamp'] = max(level['timestamp'], timestamp)

                # SR Flip check
                if level['type'] != level_type:
                    level['type'] = 'flip'
                return

        # If no nearby level, add a new one
        self.levels.append({
            'price': price,
            'timestamp': timestamp,
            'count': 1,
            'type': level_type
        })

    def detect_levels(self, df):
        """
        Run detection on the given DataFrame.
        :param df: Pandas DataFrame with 'high' and 'low' columns and datetime index or 'date' column.
        """
        if not {'high', 'low'}.issubset(df.columns):
            raise ValueError("DataFrame must contain 'high' and 'low' columns (lowercase).")

        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df = df.set_index('date')
            else:
                raise ValueError("DataFrame must have a datetime index or 'date' column.")

        self.levels.clear()

        for i in range(self.window, len(df) - self.window):
            low_slice = df['low'].iloc[i - self.window: i + self.window + 1]
            high_slice = df['high'].iloc[i - self.window: i + self.window + 1]
            current_low = df['low'].iloc[i]
            current_high = df['high'].iloc[i]
            timestamp = df.index[i]

            if current_low == low_slice.min():
                self._merge_or_add_level(timestamp, current_low, 'support')

            if current_high == high_slice.max():
                self._merge_or_add_level(timestamp, current_high, 'resistance')

        return self.get_levels()

    def get_levels(self):
        """
        Get the list of levels detected so far.
        :return: List of dicts with 'price', 'timestamp', 'count', 'type'
        """
        return sorted(self.levels, key=lambda x: x['price'])

if __name__ == '__main__':
    df = CandleDataLoader().candles('NIFTY2551524300PE', Exchange.OPTIDX, CandleLength.FIFTEEN_MIN, 5)
    print(df)
    srd = SupportResistanceDetectorV2(window=2, merge_percent=0.1)
    levels = srd.detect_levels(df)
    pprint.pprint(levels)
