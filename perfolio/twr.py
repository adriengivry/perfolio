import numpy

from itertools import groupby
from PySide6.QtCore import QDate
from perfolio.portfolio import Portfolio

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
    def calculate_twr_period(portfolio: Portfolio, period_date: QDate, previous_period_date: QDate, previous_period_portfolio: float) -> TWRPeriod:
        current_portfolio = portfolio.get_portfolio_value_at_date(period_date, True)
        period_cash_flows = portfolio.calculate_cash_flows_between(previous_period_date, period_date)

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
    def calculate_twr(portfolio: Portfolio, begin_date: QDate, end_date: QDate) -> TWRResult:
        filtered_transactions = portfolio.get_transactions_between_dates(begin_date, end_date)

        # Combine transactions per period
        periods_transactions = {key: list(group) for key, group in groupby(filtered_transactions, key=lambda t: t.date)}

        periods = list[TWRPeriod]()

        previous_portfolio = portfolio.get_portfolio_value_at_date(begin_date, False)
        previous_period_date = begin_date

        for period_date in periods_transactions.keys():
            if period_date != previous_period_date:
                period_result = TWRProcessor.calculate_twr_period(portfolio, period_date, previous_period_date, previous_portfolio)
                periods.append(period_result)
                previous_period_date = period_date
                previous_portfolio = period_result.end_portfolio_value

        if previous_period_date != end_date:
            periods.append(TWRProcessor.calculate_twr_period(portfolio, end_date, previous_period_date, previous_portfolio))

        twr = 1.0

        for period in periods:
            if not numpy.isnan(period.growth_factor):
                twr *= period.growth_factor

        return TWRResult(periods, twr - 1)
    