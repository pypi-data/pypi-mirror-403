import json

from candlestix.candleconf import Exchange


class Instrument:
    def __init__(self,
                 symbol: str,
                 instrument_key: str,
                 name: str,
                 exchange: Exchange):

        self.instrument_key = instrument_key
        self.symbol = symbol
        self.exchange = exchange
        self.name = name

    @staticmethod
    def get_exchange_from_val(val: str):
        for v in Exchange.__members__.values():
            if val.upper() == v.value:
                return v
        return None

    def __repr__(self):
        return (f'Instrument(instrument_key={self.instrument_key}, symbol={self.symbol}, exchange={self.exchange}, '
                f'name={self.name})')
