import numpy as np
from pandas import DataFrame


def is_downtrend(ohlcv: DataFrame,
                 back_candles_count: int = 5,
                 offset: int = 0,
                 last_three_candles: bool = False,
                 symbol:str = None):
    """
    Attempts to check if a stock is in downtrend by evaluating the following conditions:

    1. 70% of candles should close lower than previous candle
    2. average fall should be 0.9% per candle (for 10 candles >= 9%, for 5 candles >= 4.5%, etc.)
    3. (Optional): last three candles should be red, each one closing lower than the one before

    The third check is optional and controlled via the `last_three_candles (bool)` flag.

    The code works by scanning candles backwards starting from `(current - offset)` candle, going till
    `(current - (offset + back_candles_count))`.

    The function returns `(condition1 OR condition2 OR condition3)`

    Parameters:
        ohlcv (DataFrame): A dataframe with OHLCV data for the stock
        back_candles_count (int): number of back candle to consider for downtrend detection. Defaults to 5.
        offset (int): candle from which evaluation will be started for detection of downtrend.
                      Example: if `c` denotes the current candle and `o` denotes the offset, scanning will start
                      from `(c-o)` candle. Default = 0.
        last_three_candles (bool): boolean flag indicating if last 3 candles (from offset) in pure downtrend confirm a
                                   downtrend. It works fine for candle patterns detection, but should not be used for
                                   generic downtrend detection. Defaults to `False`.

    Returns:
        `True` if a downtrend was detected, `False` otherwise.
    """
    t = len(ohlcv) - 1
    start = offset
    end = offset + back_candles_count

    # ---- BEGIN: Last Three Candles Downtrend Check ----
    if last_three_candles:

        is_red_and_down = True
        end = offset + 3
        for i in range(start, end):
            # even if one candle closes above the previous one, condition3 will become false
            is_red_and_down = is_red_and_down and (ohlcv['close'].iloc[t - i] < ohlcv['close'].iloc[t - i - 1])

        if is_red_and_down:
            return True
    # ---- END: Last Three Candles Downtrend Check ----

    # ---- BEGIN: -0.9% fall per candle check ----
    close_pct_change = 100*(ohlcv['close'].iloc[t - start] - ohlcv['close'].iloc[t - end]) / ohlcv['close'].iloc[t - end]
    pct_change_per_candle = round(close_pct_change / back_candles_count, 2)
    condition2 = pct_change_per_candle < -0.9
    # ---- END: -0.9% fall per candle check ----

    # ---- BEGIN: 70% red candles check ----
    down_count = 0
    up_count = 0
    for i in range(start, end):
        if ohlcv['close'].iloc[t - i] < ohlcv['close'].iloc[t - i - 1]:
            down_count = down_count + 1
        elif ohlcv['close'].iloc[t - i] > ohlcv['close'].iloc[t - i - 1]:
            up_count = up_count + 1

    red_candle_ratio = round(down_count/back_candles_count, 2)
    condition3 = red_candle_ratio >= 0.7
    # ---- END: 70% red candles check ----

    # print(f'vvv {symbol}, start={ohlcv.index[t-start]}, end={ohlcv.index[t-end+1]}, fall_per_candle={condition2}, red_candle_check={condition3}, pct_change_per_candle={pct_change_per_candle}, red_candle_ratio={red_candle_ratio}')
    return condition2 or condition3
