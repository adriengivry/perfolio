import hashlib
from PySide6.QtCore import Qt, QDate
from perfolio.output import Output
from perfolio.portfolio import Portfolio

from perfolio.settings import Setting, SettingFactory
from perfolio.twr import TWRProcessor
    
# Base class for any operation
class Operation:
    def __init__(self, category, name):
        super().__init__()
        self.category = category
        self.name = name
        self.settings = None
        
    def get_hash(self) -> str:
        identifier = type(self).__name__.encode()
        return hashlib.sha256(identifier).hexdigest()

    def get_settings_desc(self) -> dict[str, Setting]:
        return {}
    
    def get(self, key):
        if key in self.settings:
            value = self.settings[key]
            return value
        else:
            return self.get_settings_desc()[key].default
    
    def get_display_name(self) -> str:
        return f"{self.category}|{self.name}"
    
    def validate(self, context, output) -> bool:
        return True

    def execute(self, context, output) -> bool:
        return True
    
    def execute_with_settings(self, settings, portfolio: Portfolio, output: Output) -> bool:
        self.settings = settings
        success = self.validate(portfolio, output) and self.execute(portfolio, output)
        self.settings = None
        return success

class OperationRegistry:
    operations = []
    
    @staticmethod
    def register(category, name):
        def decorator(cls):
            OperationRegistry.operations.append(cls(category, name))
            return cls
        return decorator
    
    @staticmethod
    def get_operation_instance(operation_class):
        for operation in OperationRegistry.operations:
            if isinstance(operation, operation_class):
                return operation
        return None
    
    @staticmethod
    def get_operation_instance_from_hash(hashcode):
        for operation in OperationRegistry.operations:
            if operation.get_hash() == hashcode:
                return operation
        return None

@OperationRegistry.register("Return Calculation", "Calculate TWR")
class CalculateTWROperation(Operation):
    def get_settings_desc(self):
        return {
            **super().get_settings_desc(),
            "from": SettingFactory.date("From", QDate.currentDate().addYears(-1)),
            "to": SettingFactory.date("To"),
           
        }
    
    def execute(self, portfolio: Portfolio, output: Output):
        start_date = self.get("from")
        end_date = self.get("to")

        # Calculate TWR
        twr = TWRProcessor.calculate_twr(portfolio, start_date, end_date)

        # Print the result
        output.log_text(f"Time-Weighted Return (TWR): {twr.value:.2%}")
        output.log_table(f"TWR (From {start_date.toString(Qt.DateFormat.ISODate)} to {end_date.toString(Qt.DateFormat.ISODate)})", ["From", "To", "Growth Factor", "Return", "Portfolio Initial Value", "Portfolio Final Value", "Cash Flow", "Gain/Loss"], [
            (
                period.start_date.toString(Qt.DateFormat.ISODate),
                period.end_date.toString(Qt.DateFormat.ISODate),
                f"{period.growth_factor:.2f}",
                f"{period.period_return:.2%}",
                f"$ {period.begin_portfolio_value:,.2f}",
                f"$ {period.end_portfolio_value:,.2f}",
                f"$ {period.cash_flow:,.2f}",
                f"$ {period.gain_loss:,.2f}"
            )
            for period in twr.periods
        ])

        return True
    
@OperationRegistry.register("Return Calculation", "Calculate MWR")
class CalculateTWROperation(Operation):
    def get_settings_desc(self):
        return {
            **super().get_settings_desc(),
            "from": SettingFactory.date("From", QDate.currentDate().addYears(-1)),
            "to": SettingFactory.date("To"),
           
        }
    
    def execute(self, portfolio: Portfolio, output: Output):
        start_date = self.get("from")
        end_date = self.get("to")

        # # Calculate TWR
        # portfolio.transactions = Finance.calculate_portfolio_value_at_date_from_transactions(portfolio.transactions,  )

        # # Print the result
        # # output.log_text(f"Money-Weighted Return (MWR): {twr.value:.2%}")
        # output.log_table(f"MWR (From {start_date.toString(Qt.DateFormat.ISODate)} to {end_date.toString(Qt.DateFormat.ISODate)})", ["From", "To", "Growth Factor", "Return", "Portfolio Initial Value", "Portfolio Final Value", "Cash Flow", "Gain/Loss"], [
        #     (
        #         period.start_date.toString(Qt.DateFormat.ISODate),
        #         period.end_date.toString(Qt.DateFormat.ISODate),
        #         f"{period.growth_factor:.2f}",
        #         f"{period.period_return:.2%}",
        #         f"$ {period.begin_portfolio_value:,.2f}",
        #         f"$ {period.end_portfolio_value:,.2f}",
        #         f"$ {period.cash_flow:,.2f}",
        #         f"$ {period.gain_loss:,.2f}"
        #     )
        #     for period in twr.periods
        # ])

        return True

@OperationRegistry.register("Portfolio Analysis", "View Holdings")
class ViewHoldingsOperation(Operation):
    def get_settings_desc(self):
        return {
            **super().get_settings_desc(),
            "date": SettingFactory.date("Date"),
        }
    
    def execute(self, portfolio: Portfolio, output: Output):
        date = self.get("date")

        holdings = portfolio.get_holdings_at_date(date, False)
        output.log_table(f"Holdings ({date.toString(Qt.DateFormat.ISODate)})", ["Symbol", "Quantity"], holdings.items())
        
        return True
    
@OperationRegistry.register("Portfolio Analysis", "View Transactions")
class ViewTransactionsOperation(Operation):
    def get_settings_desc(self):
        return {
            **super().get_settings_desc(),
            "from": SettingFactory.date("From", QDate.currentDate().addYears(-1)),
            "to": SettingFactory.date("To"),
        }
    
    def execute(self, portfolio: Portfolio, output: Output):
        from_date = self.get("from")
        to_date = self.get("to")

        transactions = portfolio.get_transactions_between_dates(from_date, to_date)
        output.log_table(f"Transactions (From {from_date.toString(Qt.DateFormat.ISODate)} to {to_date.toString(Qt.DateFormat.ISODate)})", ["Symbol", "Date", "Type", "Quantity", "Price"], [
            (
                transaction.symbol,
                transaction.date.toString(Qt.DateFormat.ISODate),
                transaction.type,
                f"{transaction.quantity:.0f}" if transaction.quantity.is_integer() else f"{transaction.quantity:.2f}",
                str(transaction.price)
            )
            for transaction in transactions
        ])
        
        return True
    
@OperationRegistry.register("Portfolio Analysis", "View Holdings Diff")
class ViewHoldingsDiffOperation(Operation):
    def get_settings_desc(self):
        return {
            **super().get_settings_desc(),
            "from": SettingFactory.date("From", QDate.currentDate().addYears(-1)),
            "to": SettingFactory.date("To"),
        }
    
    def execute(self, portfolio: Portfolio, output: Output):
        from_date = self.get("from")
        to_date = self.get("to")

        holdings_diff = portfolio.get_holdings_difference(from_date, to_date)
        output.log_table(f"Holdings Diff (From {from_date.toString(Qt.DateFormat.ISODate)} to {to_date.toString(Qt.DateFormat.ISODate)})", ["Symbol", "Difference"], holdings_diff.items())
        
        return True