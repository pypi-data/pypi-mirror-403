import logging
import os

import pandas
import pandas as pd
from pandas import DataFrame

import candlestix
from candlestix.candleconf import CandleLength, Exchange
from candlestix.time import TimeService
from candlestix.upstox import UpstoxCandleDataFetcher


class CandleDataLoader:
    """Responsible for fetching candle data."""

    def __init__(self, time_service: TimeService = None,
                 candle_data_fetcher: UpstoxCandleDataFetcher = None,
                 debug_dump_unified_candles_to_csv: bool = False):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__time_service = TimeService() if time_service is None else time_service
        self.__upstox_hist = UpstoxCandleDataFetcher() if candle_data_fetcher is None else candle_data_fetcher
        self.debug_dump_unified_candles_to_csv = debug_dump_unified_candles_to_csv

    def candles(self, symbol: str, exchange: Exchange,
                candle_length: CandleLength, duration_in_days: int = -1) -> DataFrame:

        if duration_in_days == -1:
            duration_in_days = candle_length.value.get_days_to_fetch()

        if candle_length == CandleLength.WEEK or candle_length == CandleLength.MONTH:
            raise ValueError(f'Unsupported candle_length: {candle_length.name}.')

        if duration_in_days == -1:
            duration_in_days = candle_length.value.get_days_to_fetch()

        # Do not hit historical data API if duration_in_days is 1, which is TODAY only.
        df_hist = pandas.DataFrame() if duration_in_days == 1 else self._fetch_historical_candles(symbol, exchange,
                                                                                                  candle_length,
                                                                                                  duration_in_days)
        df_today = self._fetch_today_candles(symbol, exchange, candle_length)

        # Concatenate the two DataFrames
        combined_df = df_hist if len(df_today) == 0 or df_today is None else pd.concat([df_hist, df_today])

        # Sort the DataFrame based on the datetime index
        combined_df.sort_index(ascending=True, inplace=True)

        # debug feature to dump cables for a stock if required
        if self.debug_dump_unified_candles_to_csv:
            file_name = f'debug__{symbol}-{exchange.name}_candle-{candle_length.name}.csv'
            combined_df.to_csv(os.path.join(candlestix.candlestix_conf['cache_dir'], file_name))

        return combined_df

    def _fetch_historical_candles(self, symbol: str, exchange: Exchange, candle_length: CandleLength,
                                  duration_in_days: int) -> DataFrame:
        """Fetches candles data for all historical days except today."""
        start_date = self.__time_service.get_past_date(duration_in_days)
        end_date = self.__time_service.get_past_date(1)

        # 1. check if cache file exists.
        cache_file = self._create_filename(symbol, exchange, candle_length.value.get_api_length_val(),
                                           end_date, start_date)
        df = self._load_cached_data_if_found(cache_file)
        # 2. If found, load and return right away!
        if df is not None:
            return df

        # 3a. If not, fetch data ...
        df = self.__upstox_hist.get_historical_data_for_symbol(symbol, exchange,
                                                               candle_length.value.get_api_length_val(),
                                                               end_date, start_date)

        # 3b. ... process it ...
        # Now we convert to desired candle size
        if candle_length == CandleLength.FIVE_MIN:
            df = self._resample_candles(df, '5T')
        if candle_length == CandleLength.TEN_MIN:
            df = self._resample_candles(df, '10T')
        if candle_length == CandleLength.FIFTEEN_MIN:
            df = self._resample_candles(df, '15T')
        if candle_length == CandleLength.THIRTY_MIN:
            df = self._resample_candles(df, '30T')
        if candle_length == CandleLength.ONE_HOUR:
            df = self._resample_candles(df, '60T')
        elif candle_length == CandleLength.DAY:
            df = self._resample_candles(df, '1D')

        # 3c. ... and cache it on disk.
        df.to_csv(cache_file)

        return df

    def _fetch_today_candles(self, symbol: str, exchange: Exchange, candle_length: CandleLength) -> DataFrame:
        """Fetches candle data for current day. Valid candle_lengths are ONE_MIN and THIRTY_MIN only."""

        df = self.__upstox_hist.get_today_data_for_symbol(symbol, exchange,
                                                          CandleLength.ONE_MIN.value.get_api_length_val())
        if df is not None and len(df) > 0:
            df.drop('open_interest', axis=1, inplace=True)

            # Now we convert to desired candle size
            if candle_length == CandleLength.FIVE_MIN:
                df = self._resample_candles(df, '5T')
            if candle_length == CandleLength.TEN_MIN:
                df = self._resample_candles(df, '10T')
            if candle_length == CandleLength.FIFTEEN_MIN:
                df = self._resample_candles(df, '15T')
            if candle_length == CandleLength.THIRTY_MIN:
                df = self._resample_candles(df, '30T')
            if candle_length == CandleLength.ONE_HOUR:
                df = self._resample_candles(df, '60T')
            elif candle_length == CandleLength.DAY:
                df = self._resample_candles(df, '1D')

        return df

    def _resample_candles(self, df: DataFrame, length: str):
        df_resampled = df.resample(length, origin='start').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })

        # Drop any rows with NaN values
        df_resampled.dropna(inplace=True)
        return df_resampled

    def _create_filename(self, stock: str, exchange: Exchange, candle_length: str, ed_dt: str, st_dt: str):
        file_name = stock + '_' + exchange.name + candle_length + '-' + st_dt + '_' + ed_dt + '.csv'
        file_name = f'cache__{stock}-{exchange.name}_{candle_length}__{st_dt}_{ed_dt}.csv'
        return str(os.path.join(candlestix.candlestix_conf['cache_dir'], file_name))

    def _load_cached_data_if_found(self, cache_file):
        if not os.path.isfile(cache_file):
            return None

        try:
            df = pd.read_csv(cache_file)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        except Exception as e:
            df = None
            self.__logger.warning(f'Failed to load cache file. Deleting it!: {e}', stack_info=True, exc_info=True)
            # delete the file as it may be corrupted
            os.remove(cache_file)

        return df

