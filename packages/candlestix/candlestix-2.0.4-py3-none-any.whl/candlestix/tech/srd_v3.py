import json
import pprint
import pandas as pd

from candlestix import Exchange
from candlestix.candle_loader import CandleDataLoader
from candlestix.candleconf import CandleLength


class SupportResistanceDetectorV3:
    def __init__(self, window=5, atr_multiplier=1.0):
        """
        :param window: Number of candles to check for local extrema.
        :param atr_multiplier: Multiplier of ATR used for fuzzy merging.
        """
        self.window = window
        self.atr_multiplier = atr_multiplier
        self.levels = []
        self.atr = None  # Adaptive merge range

    def _is_close(self, a, b):
        return abs(a - b) <= self.atr

    def _merge_or_add_level(self, timestamp, price, level_type):
        for level in self.levels:
            if self._is_close(price, level['price']):
                level['count'] += 1
                level['timestamp'] = max(level['timestamp'], timestamp)
                if level['type'] != level_type:
                    level['type'] = 'flip'
                return
        self.levels.append({
            'price': price,
            'timestamp': timestamp,
            'count': 1,
            'type': level_type
        })

    def detect_levels(self, df):
        if not {'high', 'low'}.issubset(df.columns):
            raise ValueError("DataFrame must contain 'high' and 'low' columns (lowercase).")

        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df = df.set_index('date')
            else:
                raise ValueError("DataFrame must have a datetime index or 'date' column.")

        # Calculate ATR using high-low-close range (simplified)
        df['hl_range'] = df['high'] - df['low']
        self.atr = df['hl_range'].rolling(window=self.window).mean().dropna().median()
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
        return sorted(self.levels, key=lambda x: x['price'])

if __name__ == '__main__':
    # df = CandleDataLoader().candles('NIFTY2551524300PE', Exchange.OPTIDX, CandleLength.FIFTEEN_MIN, 5)
    # df = CandleDataLoader().candles('NIFTY_50', Exchange.NSE, CandleLength.ONE_HOUR, 5)
    df = CandleDataLoader().candles('HAL', Exchange.NSE, CandleLength.ONE_HOUR, 21)
    print(df)
    srd = SupportResistanceDetectorV3(window=2, atr_multiplier=1.0)
    levels = srd.detect_levels(df)
    r = ''
    for x in levels:
         r= r + f'{x["price"]}|{x["count"]}\\n'  # Removes 'timestamp' if it exists
    print(r)
