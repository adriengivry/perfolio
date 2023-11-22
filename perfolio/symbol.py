import yfinance as yf 

from PySide6.QtCore import Qt, QDate
from pandas import Timestamp

class SymbolCache:
    def __init__(self, start_date: QDate, end_date: QDate, symbols: list[str]):
        self.start_date = start_date
        self.end_date = end_date
        self.symbols = symbols
        self.invalid = True

    def invalidate(self):
        self.invalid = True

    def populate(self):
        start_date_str = self.start_date.toString(Qt.DateFormat.ISODate)
        end_date_str = self.end_date.addDays(1).toString(Qt.DateFormat.ISODate)
        self.cache = yf.download(self.symbols, start=start_date_str, end=end_date_str)
        self.invalid = False

    def get_symbol_price_at_date(self, symbol: str, date: QDate, price_type='Close'):
        if self.invalid:
            self.populate()

        if price_type not in self.cache:
            raise ValueError(f"Price type {price_type} not found in cache.")

        if symbol not in self.cache[price_type]:
            raise ValueError(f"Symbol {symbol} not found in cache[{price_type}].")
        
        timestamp = Timestamp(date.toString(Qt.DateFormat.ISODate))

        if timestamp not in self.cache[price_type][symbol]:
            raise ValueError(f"Date {timestamp} not found in cache[{price_type}][{symbol}].")
        
        return self.cache[price_type][symbol][timestamp]
    