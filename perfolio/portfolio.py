from PySide6.QtCore import QDate
import numpy

from perfolio.symbol import SymbolCache

class Transaction:
    symbol: str = None
    date: QDate = None
    type: str = None
    quantity: float = None
    price: float = None

class Portfolio:
    file_path:str = None
    transactions: list[Transaction] = []
    symbol_cache: SymbolCache = None

    def clear(self):
        self.file_path = None
        self.transactions = []
        self.symbol_cache = None

    def update_symbol_cache(self):
        sorted_transactions = sorted(self.transactions, key=lambda t: t.date)
        first_transaction_date = sorted_transactions[0].date
        unique_symbols = sorted(set(transaction.symbol for transaction in self.transactions))
        self.symbol_cache = SymbolCache(first_transaction_date, QDate.currentDate(), unique_symbols)

    def get_transactions_between_dates(self, start_date: QDate, end_date: QDate) -> list[Transaction]:
        filtered_transactions = []
        
        for transaction in self.transactions:
            if start_date < transaction.date <= end_date:
                filtered_transactions.append(transaction)
        
        return filtered_transactions
    
    def get_holdings_at_date(self, target_date: QDate, at_close: bool, filter_empty_holdings: bool = True) -> dict[str, float]:
        holdings = {}

        for transaction in self.transactions:
            if (transaction.date <= target_date) if at_close else (transaction.date < target_date):
                if transaction.type == 'buy':
                    holdings[transaction.symbol] = holdings.get(transaction.symbol, 0) + int(transaction.quantity)
                elif transaction.type == 'sell':
                    holdings[transaction.symbol] = holdings.get(transaction.symbol, 0) - int(transaction.quantity)

        if filter_empty_holdings:
            holdings = {symbol: shares for symbol, shares in holdings.items() if shares != 0}

        return holdings
    
    def get_holdings_difference(self, start_date: QDate, end_date: QDate):
        start_holdings = self.get_holdings_at_date(start_date, False)
        end_holdings = self.get_holdings_at_date(end_date, True)
        common_symbols = set(start_holdings.keys()) & set(end_holdings.keys())
        holdings_difference = {symbol: end_holdings[symbol] - start_holdings[symbol] for symbol in common_symbols}
        return holdings_difference
    
    def get_portfolio_value_at_date(self, date: QDate, at_close: bool):
        total_portfolio_value = 0

        holdings = self.get_holdings_at_date(date, at_close) # Returns a dict of str, float (symbol, quantity)

        for symbol, quantity in holdings.items():
            try:
                price_at_date = self.symbol_cache.get_symbol_price_at_date(symbol, date)
                if not numpy.isnan(price_at_date):
                    total_portfolio_value += quantity * price_at_date
            except Exception as e:
                print(f"Error fetching historical price for {symbol}: {e}")

        return total_portfolio_value
    
    def calculate_cash_flows_between(self, start_date: QDate, end_date: QDate):
        transactions = self.get_transactions_between_dates(start_date, end_date)

        cash_flow = 0

        for transaction in transactions:
            amount = float(transaction.quantity) * float(transaction.price)
            if transaction.type == "sell":
                cash_flow -= amount
            elif transaction.type == "buy":
                cash_flow += amount

        return cash_flow
