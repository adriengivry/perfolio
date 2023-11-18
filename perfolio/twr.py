from datetime import timedelta
from itertools import groupby
from PySide6.QtCore import Qt, QDate
import numpy
import yfinance as yf

from perfolio.operations import Operations 
from perfolio.symbol import SymbolCache 

class TWRPeriod:
    def __init__(self, start_date: QDate, end_date: QDate, period_return: float, growth_factor: float, begin_portfolio_value: float, end_portfolio_value: float, cash_flow: float, gain_loss: float):
        self.start_date = start_date
        self.end_date = end_date
        self.period_return = period_return
        self.growth_factor = growth_factor
        self.begin_portfolio_value = begin_portfolio_value
        self.end_portfolio_value = end_portfolio_value
        self.cash_flow = cash_flow
        self.gain_loss = gain_loss

class TWRResult:
    def __init__(self, periods: list[TWRPeriod], value: float):
        self.periods = periods
        self.value = value

class TWRProcessor:
    @staticmethod
    def calculate_twr_period(all_transactions, symbol_cache: SymbolCache, period_date: QDate, previous_period_date: QDate, previous_period_portfolio: float) -> TWRPeriod:
        current_portfolio = Operations.calculate_portfolio_value_at_date_from_transactions(all_transactions, symbol_cache, period_date, True)
        period_cash_flows = Operations.calculate_cash_flows(Operations.get_transactions_between_dates(all_transactions, previous_period_date, period_date))

        if previous_period_portfolio != 0:
            growth_factor = (current_portfolio - period_cash_flows) / previous_period_portfolio
            period_return = ((current_portfolio - period_cash_flows) - previous_period_portfolio) / previous_period_portfolio
        else:
            growth_factor = 1
            period_return = 0

        gain_loss =  current_portfolio - previous_period_portfolio - period_cash_flows

        return TWRPeriod(
            previous_period_date,
            period_date,
            period_return,
            growth_factor,
            previous_period_portfolio,
            current_portfolio,
            period_cash_flows,
            gain_loss
        )
    
    @staticmethod
    def calculate_twr(transactions, begin_date: QDate, end_date: QDate) -> TWRResult:
        filtered_transactions = Operations.get_transactions_between_dates(transactions, begin_date, end_date)

        unique_symbols = sorted(set(transaction[0] for transaction in transactions))
        symbol_cache = SymbolCache(begin_date, end_date, unique_symbols)

        # Combine transactions per period
        periods_transactions = {key: list(group) for key, group in groupby(filtered_transactions, key=lambda x: x[1])}

        periods = list[TWRPeriod]()

        previous_portfolio = Operations.calculate_portfolio_value_at_date_from_transactions(transactions, symbol_cache, begin_date, False)
        previous_period_date = begin_date

        for period_date_str in periods_transactions.keys():
            period_date = QDate.fromString(period_date_str, "yyyy-MM-dd")

            if (period_date != previous_period_date):
                period_result = TWRProcessor.calculate_twr_period(transactions, symbol_cache, period_date, previous_period_date, previous_portfolio)
                periods.append(period_result)
                previous_period_date = period_date
                previous_portfolio = period_result.end_portfolio_value

        if (previous_period_date != end_date):
            periods.append(TWRProcessor.calculate_twr_period(transactions, symbol_cache, end_date, previous_period_date, previous_portfolio))

        twr = 1.0

        for period in periods:
            if not numpy.isnan(period.growth_factor):
                twr *= period.growth_factor

        return TWRResult(periods, twr - 1)
    