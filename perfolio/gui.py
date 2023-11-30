import os
import csv

from PySide6 import QtCore
from PySide6.QtCore import Qt, QUrl, QDate
from PySide6.QtGui import QAction, QFont, QFontDatabase, QIcon, QPainter, QPixmap, QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QLayout, QMainWindow, QMessageBox,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFormLayout, QDockWidget, QStyle,
    QTextEdit, QApplication, QTableWidget,
    QFileDialog, QTableWidgetItem, QHeaderView,
    QGroupBox, QTabWidget
)
import perfolio
from perfolio.output import Output
from perfolio.portfolio import Portfolio, Transaction

from perfolio.settings import AppSettings
from perfolio.utils import Utils
from perfolio.operations import OperationRegistry, Operation

class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Settings")
        
        layout = QFormLayout()
        self.setLayout(layout)
        
        self.controls = dict[str, QWidget]()
        
        for id, setting in AppSettings.settings_desc.items():
            label = QLabel(setting.label)
            self.controls[id] = setting.create_widget(id)
            layout.addRow(label, self.controls[id])

        buttons_layout = QHBoxLayout()  # Horizontal layout for buttons
        
        self.save_button = QPushButton("Apply Settings")
        self.save_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.save_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        self.save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(self.save_button)

        self.load_defaults_button = QPushButton("Load Default Settings")
        self.load_defaults_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.load_defaults_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton))
        self.load_defaults_button.clicked.connect(self.ask_load_default_settings)
        buttons_layout.addWidget(self.load_defaults_button)
        
        self.open_settings_button = QPushButton("Open Settings File")
        self.open_settings_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.open_settings_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.open_settings_button.clicked.connect(self.open_settings_file)
        
        buttons_layout.addWidget(self.open_settings_button)

        layout.addRow(buttons_layout)

        # Load settings into controls
        self.load_settings()

    def load_settings(self, force_default=False):
        for id, setting in AppSettings.settings_desc.items():
            setting.set_to_widget(self.controls[id], AppSettings.get(id, force_default))
            
    def save_settings(self):
        for id, setting in AppSettings.settings_desc.items():
            AppSettings.set(id, setting.get_from_widget(self.controls[id]))
            
        AppSettings.save_settings()
        self.close()
        
    def ask_load_default_settings(self):
        # Display a confirmation dialog
        confirm_dialog = QMessageBox()
        confirm_dialog.setIcon(QMessageBox.Icon.Question)
        confirm_dialog.setWindowTitle("Confirm Load Default Settings")
        confirm_dialog.setText("Are you sure you want to load the default settings?\n"
                               "This action will discard your current settings.")
        confirm_dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm_dialog.setDefaultButton(QMessageBox.StandardButton.No)

        result = confirm_dialog.exec()

        if result == QMessageBox.StandardButton.Yes:
            self.load_settings(True)
            
    def open_settings_file(self):
        settings_folder = Utils.get_appdata_path()
        settings_file = os.path.join(settings_folder, "settings.json")

        if os.path.exists(settings_file):
            try:
                os.system(f"start {settings_file}")  # Open with default text editor
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "Settings file not found.")

class OperationSettingsDialog(QDialog):
    def __init__(self, portfolio: Portfolio, output: Output, operation: Operation):
        super().__init__()

        self.portfolio = portfolio
        self.output = output
        self.operation = operation

        self.setWindowTitle(f"{operation.name} Settings")
        
        layout = QFormLayout()
        self.setLayout(layout)
        
        self.controls = dict[str, QWidget]()
        
        for id, setting in operation.get_settings_desc().items():
            label = QLabel(setting.label)
            self.controls[id] = setting.create_widget(id)
            layout.addRow(label, self.controls[id])

        buttons_layout = QHBoxLayout()  # Horizontal layout for buttons
        
        self.run_button = QPushButton("Run")
        self.run_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.run_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.run_button.clicked.connect(self.on_run)
        buttons_layout.addWidget(self.run_button)
        
        layout.addRow(buttons_layout)

    def on_run(self):
        settings = self.get_settings()
        self.run_button.setDisabled(True)
        self.operation.execute_with_settings(settings, self.portfolio, self.output)
        self.close()

    def get_settings(self) -> dict:
        settings = {}

        for key, setting in self.operation.get_settings_desc().items():
            settings[key] = setting.get_from_widget(self.controls[key])
            
        return settings

class Panel(QDockWidget):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setWidget(QWidget())
        self.widget().setLayout(self.create_layout())
        
    # Create and return the main layout of the panel
    def create_layout(self) -> QLayout:
        pass

class OutputPanel(Panel):    
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.clear_text()
        
    def create_output(self) -> QTextEdit:
        # Setup output font
        monospace_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        monospace_font.setFamily("Consolas")
        
        # Create output widget
        output = QTextEdit()
        output.setFont(monospace_font)
        output.setReadOnly(True)
        output.setAcceptRichText(False)
        output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        output.setMaximumHeight(128)
        
        return output
    
    def create_controls(self) -> QLayout:
        # Create controls
        self.clear_button = QPushButton("Clear Output")
        self.scroll_to_top_button = QPushButton("Scroll to Top")
        self.scroll_to_bottom_button = QPushButton("Scroll to Bottom")
        self.copy_button = QPushButton("Copy to Clipboard")
        
        # Controls Icons & Settings
        self.clear_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)) 
        self.scroll_to_top_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
        self.scroll_to_bottom_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown)) 
        self.copy_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        
        # Controls Callbacks
        self.clear_button.clicked.connect(self.clear_text)
        self.scroll_to_bottom_button.clicked.connect(self.scroll_to_bottom)
        self.scroll_to_top_button.clicked.connect(self.scroll_to_top)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        
        # Controls Layout
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.clear_button)
        controls_layout.addWidget(self.scroll_to_top_button)
        controls_layout.addWidget(self.scroll_to_bottom_button)
        controls_layout.addWidget(self.copy_button)
        
        return controls_layout
        
    def create_layout(self):
        layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        
        self.output = self.create_output()
        controls_layout = self.create_controls()
        
        layout.addWidget(self.tabs)
        layout.addWidget(self.output)
        layout.addLayout(controls_layout)
        
        return layout
    
    def close_tab(self, index):
        self.tabs.removeTab(index)
    
    def append_table(self, name: str, headers: list[str], data: list[tuple]):
        table = QTableWidget()
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        for rowIndex, entry in enumerate(data):
            table.insertRow(rowIndex)
            for col, value in enumerate(entry):
                    item = QTableWidgetItem(str(value))
                    table.setItem(rowIndex, col, item)

        table.resizeColumnsToContents()
        self.tabs.addTab(table, name)
        self.tabs.setCurrentWidget(table)

    def append_text(self, text):
        if text != None:
            self.clear_button.setEnabled(True)
            self.scroll_to_top_button.setEnabled(True)
            self.scroll_to_bottom_button.setEnabled(True)
            self.copy_button.setEnabled(True)
            self.output.append(text)

    def clear_text(self):
        self.clear_button.setEnabled(False)
        self.scroll_to_top_button.setEnabled(False)
        self.scroll_to_bottom_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self.output.clear()

    def scroll_to_bottom(self):
        max_y_scroll = self.output.verticalScrollBar().maximum()
        self.output.verticalScrollBar().setValue(max_y_scroll)
        self.output.horizontalScrollBar().setValue(0)
        
    def scroll_to_top(self):
        self.output.verticalScrollBar().setValue(0)
        self.output.horizontalScrollBar().setValue(0)
        
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output.toPlainText())
    
class TransactionPanel(Panel):
    def __init__(self, title, parent, portfolio: Portfolio):
        self.portfolio = portfolio
        super().__init__(title, parent)

    def setup_table(self):
        self.transactions_table.horizontalHeader().setStretchLastSection(False)
        self.transactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.transactions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.transactions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
    def create_layout(self):
        layout = QVBoxLayout()

        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(5)
        self.transactions_table.setHorizontalHeaderLabels(["Symbol", "Date", "Type", "Quantity", "Price"])
        self.setup_table()
        layout.addWidget(self.transactions_table)
        
        last_opened_portfolio = Utils.retrieve_last_opened_portfolio()
        self.load_data_from_csv(last_opened_portfolio)

        load_button = QPushButton("Load from CSV")
        load_button.clicked.connect(self.load_data_from_csv_dialog)
        layout.addWidget(load_button)

        reload_button = QPushButton("Reload CSV")
        reload_button.clicked.connect(self.reload)
        layout.addWidget(reload_button)

        reload_historical_prices = QPushButton("Reload Historical Prices")
        reload_historical_prices.clicked.connect(self.reload_historical_prices)
        layout.addWidget(reload_historical_prices)
        
        return layout

    def load_data_from_csv_dialog(self):
        # Open a file dialog to get the path to the CSV file
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        self.load_data_from_csv(file_path)

    def load_data_from_csv(self, file_path):
        if file_path:
            print(f"Loading data from CSV file: {file_path}")

            # Load data from the CSV file and update the table
            try:
                self.portfolio.clear()
                self.portfolio.file_path = file_path

                with open(file_path, 'r', newline='') as csvfile:
                    csvreader = csv.reader(csvfile)
                    headers = [header.lower() for header in next(csvreader)]

                    # Mapping for header variations
                    header_mapping = {
                        'date': ['date', 'dt', 'dte', 'de', 'day', 'at', 'dy'],
                        'symbol': ['symbol', 'ticker', 'sym', 'sbl', 'symbols'],
                        'type': ['type', 'transaction', 'trz', 'tpe'],
                        'quantity': ['quantity', 'qty', 'qt', 'amount', 'volume', 'amnt', 'shares'],
                        'price': ['price', 'prc', 'pc', 'cost']
                    }
                    
                    for row in csvreader:
                        transaction = Transaction()

                        # Process each header and fill in the transaction attributes
                        for attribute, variations in header_mapping.items():
                            for variation in variations:
                                if variation in headers:
                                    index = headers.index(variation)
                                    value = row[index]

                                    # Special handling for 'date' and 'quantity'
                                    if attribute == 'date':
                                        value = Utils.convert_date_format(value)
                                        transaction.date = QDate.fromString(value, Qt.DateFormat.ISODate)
                                    elif attribute == 'quantity':
                                        transaction.quantity = float(value)
                                    else:
                                        setattr(transaction, attribute, value)
                                    break

                        self.portfolio.transactions.append(transaction)

                self.on_portfolio_updated()

            except Exception as e:
                print(f"Error loading CSV file: {e}")

    def on_portfolio_updated(self):
        auto_load_prices = AppSettings.get("auto_load_historical_prices")
        self.portfolio.update_symbol_cache(auto_load_prices)

        Utils.store_last_opened_portfolio(self.portfolio.file_path)
        
        self.load_data_to_table([
            (
            transaction.symbol,
            transaction.date.toString(Qt.DateFormat.ISODate),
            transaction.type,
            f"{transaction.quantity:.0f}" if transaction.quantity.is_integer() else f"{transaction.quantity:.2f}",
            str(transaction.price)
            )
            for transaction in self.portfolio.transactions
        ])
    
    def reload(self):
        self.load_data_from_csv(self.portfolio.file_path)

    def reload_historical_prices(self):
        self.portfolio.symbol_cache.populate()

    def load_data_to_table(self, data):
        # Clear existing data
        self.transactions_table.setRowCount(0)

        # Load data to the table
        for row, transaction in enumerate(data):
            self.transactions_table.insertRow(row)
            for col, value in enumerate(transaction):
                item = QTableWidgetItem(str(value))
                self.transactions_table.setItem(row, col, item)

        self.transactions_table.resizeColumnsToContents()

    def get_all_transactions(self):
        all_transactions = []

        for row in range(self.transactions_table.rowCount()):
            transaction = []
            for col in range(self.transactions_table.columnCount()):
                item = self.transactions_table.item(row, col)
                transaction.append(item.text())
            all_transactions.append(tuple(transaction))

        return all_transactions

class OperationPanel(QDockWidget):
    def __init__(self, title, parent, portfolio: Portfolio, output: Output):
        super().__init__(title, parent)
        self.portfolio = portfolio
        self.output = output
        self.transactions = []
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setWidget(QWidget())
        self.widget().setLayout(self.create_layout())

    def open_operation_settings_dialog(self, portfolio: Portfolio, output: Output, operation: Operation):
        settings_dialog = OperationSettingsDialog(portfolio, output, operation)
        main_window_size = self.size()
        dialog_width = main_window_size.width() // 2
        settings_dialog.setFixedWidth(max(dialog_width, 450))
        settings_dialog.exec()

    def create_layout(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        categories = {}

        for operation in OperationRegistry.operations:
            categories.setdefault(operation.category, []).append(operation)

        # Define a helper function to create a lambda function with a default argument
        def create_operation_setting_dialog_lambda(operation):
            return lambda: self.open_operation_settings_dialog(self.portfolio, self.output, operation)

        for category, operations in categories.items():
            # Create a group box
            group_box = QGroupBox(category)
            group_layout = QVBoxLayout(group_box)

            for operation in operations:
                operation_button = QPushButton(operation.name)
                operation_button.clicked.connect(create_operation_setting_dialog_lambda(operation))
                group_layout.addWidget(operation_button)
            
            layout.addWidget(group_box)

        return layout
    
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_menu()
        
        emoji_font = QFont("Segoe UI Emoji", 64)  # Use an emoji-supporting font
        pixmap_size = 98
        emoji_pixmap = QPixmap(pixmap_size, pixmap_size)
        emoji_pixmap.fill(QtCore.Qt.GlobalColor.transparent)  # Make pixmap transparent

        painter = QPainter(emoji_pixmap)
        painter.setFont(emoji_font)
        painter.drawText(emoji_pixmap.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "📊")  # Replace with your emoji
        painter.end()

        # Set window icon
        self.setWindowIcon(QIcon(emoji_pixmap))
        
    def init_ui(self):
        self.setWindowTitle(f"Perfolio")

        self.portfolio = Portfolio()
        self.output = Output()
        
        # Create panels
        self.transaction_panel = TransactionPanel("Transactions", self, self.portfolio)
        self.output_panel = OutputPanel("Output", self)
        self.operation_panel = OperationPanel("Operations", self, self.portfolio, self.output)

        self.output.register_callbacks(
            self.output_panel.append_text,
            self.output_panel.append_table
        )

        # Setup docking
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.transaction_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.output_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.operation_panel)
        self.setCentralWidget(self.output_panel)
        
    def init_menu(self):
        menu_bar = self.menuBar()
        
        file_menu = menu_bar.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        edit_menu = menu_bar.addMenu("Edit")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        edit_menu.addAction(settings_action)

        help_menu = menu_bar.addMenu("Help")

        report_issue_action = QAction("Report Issue", self)
        report_issue_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/adriengivry/perfolio/issues/new")))
        help_menu.addAction(report_issue_action)

        open_repository_action = QAction("Open GitHub Repository", self)
        open_repository_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/adriengivry/perfolio")))
        help_menu.addAction(open_repository_action)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.open_about)
        help_menu.addAction(about_action)
        
    def show_popup(self, title, message, icon):
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
        
    def open_settings(self):
        settings_dialog = SettingsDialog()
        main_window_size = self.size()
        dialog_width = main_window_size.width() // 2
        settings_dialog.setFixedWidth(max(dialog_width, 450))
        settings_dialog.exec()
        
    def open_about(self):
        self.show_popup("About", f"Developed by Adrien GIVRY under MIT license.\nPerfolio version: {perfolio.__version__}", QMessageBox.Icon.Information)
        