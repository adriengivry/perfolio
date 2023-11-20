from datetime import timedelta
from itertools import groupby
from PySide6.QtCore import Qt, QDate
import numpy
import yfinance as yf
import pandas as pd

from perfolio.symbol import SymbolCache

class Finance:
    @staticmethod
    def get_transactions_between_dates(transactions, start_date: QDate, end_date: QDate):
        filtered_transactions = []
        
        for transaction in transactions:
            transaction_date = QDate.fromString(transaction[1], Qt.DateFormat.ISODate)
            if start_date < transaction_date <= end_date:
                filtered_transactions.append(transaction)
        
        return filtered_transactions
    
    @staticmethod
    def get_holdings_at_date(transactions, target_date: QDate, at_close: bool):
        # Create a dictionary to store the share count for each symbol
        portfolio = {}

        # Iterate through each transaction
        for transaction in transactions:
            symbol, date, transaction_type, qty, price = transaction
            transaction_date = QDate.fromString(date, 'yyyy-MM-dd')

            # Check if the transaction occurred on or before the target date
            if (transaction_date <= target_date) if at_close else (transaction_date < target_date):
                # Update share count based on buy/sell transactions
                if transaction_type == 'buy':
                    portfolio[symbol] = portfolio.get(symbol, 0) + int(qty)
                elif transaction_type == 'sell':
                    portfolio[symbol] = portfolio.get(symbol, 0) - int(qty)

        # Filter out symbols with zero share count
        result = [[symbol, share_count] for symbol, share_count in portfolio.items() if share_count > 0]

        return result
    
    @staticmethod
    def get_portfolio_diff(transactions, start_date: QDate, end_date: QDate):
        # Calculate the portfolio at the start and end dates
        start_portfolio = Finance.get_holdings_at_date(transactions, start_date, False)
        end_portfolio = Finance.get_holdings_at_date(transactions, end_date, True)

        # Create a dictionary to store the share count for each symbol
        start_portfolio_dict = dict(start_portfolio)
        end_portfolio_dict = dict(end_portfolio)

        # Create a list to store the diff output
        diff_output = []

        # Iterate through symbols in the end portfolio
        for symbol, end_qty in end_portfolio_dict.items():
            start_qty = start_portfolio_dict.get(symbol, 0)

            # Calculate the difference and add to the diff output
            diff_output.append([symbol, start_qty, end_qty, end_qty - start_qty])

        return diff_output
    
    @staticmethod
    def calculate_portfolio_value_at_date_from_transactions(all_transactions, symbol_cache: SymbolCache, date: QDate, at_close: bool):
        return Finance.calculate_portfolio_value_at_date(
            Finance.get_holdings_at_date(all_transactions, date, at_close),
            symbol_cache,
            date,
            "Close"
        )
    
    @staticmethod
    def calculate_portfolio_value_at_date(symbol_quantities, symbol_cache: SymbolCache, date: QDate, at: str = "Adj Close"):
        total_portfolio_value = 0

        for symbol, quantity in symbol_quantities:
            try:
                price_at_date = symbol_cache.get_symbol_price_at_date(symbol, date, price_type=at)
                if not numpy.isnan(price_at_date):
                    total_portfolio_value += quantity * price_at_date
            except Exception as e:
                print(f"Error fetching historical price for {symbol}: {e}")

        return total_portfolio_value
    
    @staticmethod
    def calculate_cash_flows(transactions):
        cash_flow = 0

        for transaction in transactions:
            symbol, date, type, quantity, price = transaction

            amount = float(quantity) * float(price)

            if type == "sell":
                cash_flow -= amount
            elif type == "buy":
                cash_flow += amount

        return cash_flow
    