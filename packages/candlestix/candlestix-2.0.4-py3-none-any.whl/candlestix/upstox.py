from __future__ import print_function

import csv
import datetime
import logging
import os
import time

import pandas as pd
import upstox_client
from upstox_client.rest import ApiException

import candlestix
from candlestix import Instrument
from candlestix.candleconf import Exchange, Constants


class UpstoxCandleDataFetcher:
    def __init__(self):
        self.__logger = logging.getLogger(self.__class__.__name__)

    def get_historical_data_for_symbol(self, symbol: str,
                                       exchange: Exchange,
                                       interval: str,
                                       to_date: str,
                                       from_date: str) -> pd.DataFrame:

        instrument = self._fetch_instrument(symbol, exchange)

        if self.__logger.isEnabledFor(logging.DEBUG):
            self.__logger.debug(f'API >> symbol={symbol}, exchange={exchange}, instrument_token={instrument}, '
                                f'interval={interval}, to_date={to_date}, from_date={from_date}')
        if instrument is None:
            raise ValueError(f'No instrument_token found for symbol={symbol} exchange={exchange.value}')
        return self.get_historical_data_for_inst_key(instrument.instrument_key, interval, to_date, from_date)

    def get_today_data_for_symbol(self, symbol: str,
                                  exchange: Exchange,
                                  interval: str) -> pd.DataFrame:
        instrument = self._fetch_instrument(symbol, exchange)
        return self.get_today_data_for_inst_key(instrument.instrument_key, interval)

    def get_historical_data_for_inst_key(self, instrument_key: str,
                                         interval: str,
                                         to_date: str,
                                         from_date: str) -> pd.DataFrame:
        api_instance = upstox_client.HistoryApi(upstox_client.ApiClient())

        t_0 = time.time()
        t_1 = 0
        ohlcv = None
        try:
            # Historical candle data
            api_response = api_instance.get_historical_candle_data1(instrument_key, interval, to_date, from_date,
                                                                    Constants.API_VERSION)
            t_1 = time.time()

            candles_data = api_response.data.candles

            # The edge condition handles edge case of IPO being launched today :-)
            # So no data will be available in history API.
            if len(candles_data) == 0:
                return pd.DataFrame()

            ohlcv = pd.DataFrame(candles_data)
            # Reverse the order of rows in-place. We want the earliest date to be on top
            ohlcv.iloc[:] = ohlcv.iloc[::-1].values
            ohlcv.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'open_interest']
            ohlcv.drop('open_interest', axis=1, inplace=True)
            ohlcv['date'] = pd.to_datetime(ohlcv['date'])
            ohlcv.set_index("date", inplace=True)
        except ApiException as e:
            ohlcv = None
            self.__logger.error(f"{instrument_key}: get_historical_data_for_inst_key: API call failed:"
                                f"{os.linesep} {str(e)}")
        finally:
            t_2 = time.time()
            if self.__logger.isEnabledFor(logging.DEBUG):
                self.__logger.debug(f'hist candle data: {(t_1 - t_0) * 10 ** 3} ms | '
                                    f'df creation: {(t_2 - t_1) * 10 ** 3} ms')

        return ohlcv

    def get_today_data_for_inst_key(self, instrument_key: str, interval: str):

        api_instance = upstox_client.HistoryApi(upstox_client.ApiClient())
        ohlcv = self.__create_empty_ohlcv_df()

        t_0 = time.time()
        t_1 = 0
        try:
            # Today's candle data
            api_response = api_instance.get_intra_day_candle_data(instrument_key, interval, Constants.API_VERSION)
            t_1 = time.time()

            candles_data = api_response.data.candles
            ohlcv.drop('open_interest', axis=1, inplace=True)
            if len(candles_data) > 0:
                # Upstox fixed the issue but keeping it commented here, just in case it happens again in future
                # self.remove_ohlcv_entries_not_from_today(candles_data)
                ohlcv = pd.DataFrame(candles_data)
                ohlcv.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'open_interest']
                # Reverse the order of rows in-place. We want the earliest date to be on top
                ohlcv.iloc[:] = ohlcv.iloc[::-1].values
            ohlcv['date'] = pd.to_datetime(ohlcv['date'])
            ohlcv.set_index("date", inplace=True)
        except ApiException as e:
            ohlcv = None
            self.__logger.error(f"{instrument_key}: get_today_data_for_inst_key: API call failed{os.linesep} {str(e)}")
        finally:
            t_2 = time.time()
            if self.__logger.isEnabledFor(logging.DEBUG):
                self.__logger.debug(f'today candle data: {round((t_1 - t_0) * 10 ** 3, 2)} ms | '
                                    f'df creation: {round((t_2 - t_1) * 10 ** 3, 2)} ms')

        return ohlcv

    def __create_empty_ohlcv_df(self):
        """
        Create an empty OHLCV DataFrame with columns ['date', 'open', 'high', 'low', 'close', 'volume', 'open_interest'].
        """
        columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'open_interest']
        empty_df = pd.DataFrame(columns=columns)
        empty_df['date'] = pd.to_datetime(empty_df['date'])  # Convert 'date' column to datetime dtype
        return empty_df

    # Required because upstox API was returning one element from previous day for
    # intraday data. I don't know when will they fix it. So putting in a safe solution
    # which will work even when they fix it.
    def remove_ohlcv_entries_not_from_today(self, raw_ohlcv_candle_date: list):
        today_date_str = datetime.date.today().strftime('%Y-%m-%d') + 'T'

        indices_to_delete = []
        for i in range(0, len(raw_ohlcv_candle_date)):
            if not raw_ohlcv_candle_date[i][0].startswith(today_date_str):
                indices_to_delete.append(i)

        indices_to_delete.sort(reverse=True)
        print(indices_to_delete)
        for i in indices_to_delete:
            raw_ohlcv_candle_date.pop(i)

    def _fetch_instrument(self, symbol: str, exchange: Exchange) -> Instrument:
        if exchange == Exchange.NSE or exchange == Exchange.NSE_INDEX:
            return candlestix.nse_lookup.get(symbol)
        elif exchange == Exchange.BSE or exchange == Exchange.BSE_INDEX:
            return candlestix.bse_lookup.get(symbol)
        elif exchange == Exchange.OPTIDX or exchange == Exchange.OPTSTK:
            return self.__find_option_in_csv(symbol, exchange)
        else:
            return None

    def __find_option_in_csv(self, symbol, exchange):
        file_path = candlestix.download_and_unzip_gzip_file()
        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[9] == exchange.name and row[2] == symbol:
                    return Instrument(symbol, row[0], '', Exchange.OPTIDX)
        return None  # Return None if no matching row is found


