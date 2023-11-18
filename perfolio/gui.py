import os
import csv

from PySide6 import QtCore
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QAction, QFont, QFontDatabase, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QDialog, QLayout, QMainWindow, QMessageBox,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFormLayout, QDockWidget, QStyle,
    QTextEdit, QApplication, QTableWidget,
    QFileDialog, QTableWidgetItem, QHeaderView,
    QDateEdit
)

from perfolio.settings import AppSettings
from perfolio.utils import Utils
from perfolio.operations import Operations
from perfolio.twr import TWRProcessor, TWRResult, TWRPeriod

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
        settings_folder = Utils.get_mcsgui_appdata_path()
        settings_file = os.path.join(settings_folder, "settings.json")

        if os.path.exists(settings_file):
            try:
                os.system(f"start {settings_file}")  # Open with default text editor
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "Settings file not found.")

class Panel(QDockWidget):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setWidget(QWidget())
        self.widget().setLayout(self.create_layout())
        
    # Create and return the main layout of the panel
    def create_layout(self) -> QLayout:
        pass
    
class TransactionPanel(Panel):
    def __init__(self, title, parent):
        super().__init__(title, parent)

    def setup_table(self):
        # Set table properties
        self.transactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.transactions_table.horizontalHeader().setStretchLastSection(True)
        self.transactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.transactions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.transactions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
    def create_layout(self):
        layout = QVBoxLayout()

        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(5)
        self.transactions_table.setHorizontalHeaderLabels(["Symbol", "Date", "Type", "Qty", "Price"])
        self.setup_table()

        # Add a label or other widgets if needed
        title_label = QLabel("Stock Market Transactions")
        layout.addWidget(title_label)

        layout.addWidget(self.transactions_table)

        # Add the button to load data from a CSV file
        load_button = QPushButton("Load from CSV")
        load_button.clicked.connect(self.load_data_from_csv)
        layout.addWidget(load_button)

        # Add any additional widgets or buttons if needed
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_table)
        layout.addWidget(refresh_button)
        
        return layout

    def load_data_from_csv(self):
        # Open a file dialog to get the path to the CSV file
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")

        if file_path:
            print(f"Loading data from CSV file: {file_path}")

            # Load data from the CSV file and update the table
            try:
                with open(file_path, 'r', newline='') as csvfile:
                    csvreader = csv.reader(csvfile)
                    headers = next(csvreader)
                    data = [row for row in csvreader]

                self.load_data_to_table(data)

            except Exception as e:
                print(f"Error loading CSV file: {e}")
    
    def refresh_table(self):
        # Implement refresh logic here if needed
        pass

    def load_data_to_table(self, data):
        # Clear existing data
        self.transactions_table.setRowCount(0)

        # Load data to the table
        for row, transaction in enumerate(data):
            self.transactions_table.insertRow(row)
            for col, value in enumerate(transaction):
                item = QTableWidgetItem(str(value))
                self.transactions_table.setItem(row, col, item)

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
    def __init__(self, title, parent, transactionPanel, outputPanel):
        super().__init__(title, parent)
        self.transactionPanel = transactionPanel
        self.outputPanel = outputPanel
        self.transactions = []
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setWidget(QWidget())
        self.widget().setLayout(self.create_layout())

    def create_layout(self):
        layout = QVBoxLayout()

        # Add date selection widgets
        date_layout = QHBoxLayout()

        start_label = QLabel("Perdiod Start Date:")
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1))  # Set default to one year ago
        date_layout.addWidget(start_label)
        date_layout.addWidget(self.start_date_edit)

        end_label = QLabel("Period End Date:")
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(end_label)
        date_layout.addWidget(self.end_date_edit)

        layout.addLayout(date_layout) 

        # Add a button to retrieve transactions
        load_transactions_button = QPushButton("Load Transactions")
        load_transactions_button.clicked.connect(self.retrieve_transactions)
        layout.addWidget(load_transactions_button)

        # Add a table to display retrieved transactions
        self.table = QTableWidget()
        layout.addWidget(self.table)

        # Add a button to calculate TWR
        calculate_twr_button = QPushButton("Calculate TWR")
        calculate_twr_button.clicked.connect(self.calculate_twr)
        layout.addWidget(calculate_twr_button)

        # Add a button to load the start portfolio
        load_start_portfolio_button = QPushButton("Load Start Portfolio")
        load_start_portfolio_button.clicked.connect(self.load_start_portfolio)
        layout.addWidget(load_start_portfolio_button)

        # Add a button to load the end portfolio
        load_end_portfolio_button = QPushButton("Load End Portfolio")
        load_end_portfolio_button.clicked.connect(self.load_end_portfolio)
        layout.addWidget(load_end_portfolio_button)

        # Add a button to load the end portfolio
        load_diff_portfolio_button = QPushButton("Load Diff Portfolio")
        load_diff_portfolio_button.clicked.connect(self.load_diff_portfolio)
        layout.addWidget(load_diff_portfolio_button)

        return layout
    
    def calculate_twr(self):
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()

        # Calculate TWR
        all_transactions = self.transactionPanel.get_all_transactions()
        twr = TWRProcessor.calculate_twr(all_transactions,start_date, end_date)

        # Print the result
        self.outputPanel.append(f"Time-Weighted Return (TWR): {twr.value:.2%}")
        self.populate_table_with_twr_periods(twr.periods)

    def load_start_portfolio(self):
        all_transactions = self.transactionPanel.get_all_transactions()
        portfolio = Operations.get_portfolio_at_date(all_transactions, self.start_date_edit.date(), False)
        self.populate_table_with_portfolio(portfolio)

    def load_end_portfolio(self):
        all_transactions = self.transactionPanel.get_all_transactions()
        portfolio = Operations.get_portfolio_at_date(all_transactions, self.end_date_edit.date(), True)
        self.populate_table_with_portfolio(portfolio)

    def load_diff_portfolio(self):
        all_transactions = self.transactionPanel.get_all_transactions()
        portfolio = Operations.get_portfolio_diff(all_transactions, self.start_date_edit.date(), self.end_date_edit.date())
        self.populate_table_with_portfolio_diff(portfolio)

    def retrieve_transactions(self):
        # Implement logic to retrieve transactions between the selected dates
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()

        all_transactions = self.transactionPanel.get_all_transactions()
        self.transactions = Operations.get_transactions_between_dates(all_transactions, start_date, end_date)
    
        # Update the table with retrieved transactions
        self.populate_table_with_transactions(self.transactions)

    def populate_table_with_portfolio(self, portfolio):
        # Clear existing data
        self.table.setRowCount(0)

        # Setup table structure
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Symbol", "Qty"])

        # Load retrieved transactions to the table
        for row, entry in enumerate(portfolio):
            self.table.insertRow(row)
            for col, value in enumerate(entry):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)

    def populate_table_with_portfolio_diff(self, portfolio):
        # Clear existing data
        self.table.setRowCount(0)

        # Setup table structure
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Symbol", "Start Qty", "End Qty", "Diff"])

        # Load retrieved transactions to the table
        for row, entry in enumerate(portfolio):
            self.table.insertRow(row)
            for col, value in enumerate(entry):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)

    def populate_table_with_transactions(self, transactions):
        # Clear existing data
        self.table.setRowCount(0)

        # Setup table structure
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Symbol", "Date", "Type", "Qty", "Price"])

        # Load retrieved transactions to the table
        for row, transaction in enumerate(transactions):
            self.table.insertRow(row)
            for col, value in enumerate(transaction):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)

    def populate_table_with_twr_periods(self, periods: list[TWRPeriod]):
        self.table.setRowCount(0)
        # Setup table structure
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["From", "To", "Growth Factor", "Return", "Portfolio Initial Value", "Portfolio Final Value", "Cash Flow", "Gain/Loss"])

        # Load periods to the table
        for row, period in enumerate(periods):
            self.table.insertRow(row)
            values = [
                period.start_date.toString(Qt.DateFormat.ISODate),
                period.end_date.toString(Qt.DateFormat.ISODate),
                f"{period.growth_factor:.2f}",
                f"{period.period_return:.2%}",
                f"$ {period.begin_portfolio_value:,.2f}",
                f"$ {period.end_portfolio_value:,.2f}",
                f"$ {period.cash_flow:,.2f}",
                f"$ {period.gain_loss:,.2f}"
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)

    
class OutputPanel(Panel):    
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.clear()
        
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
        self.clear_button.clicked.connect(self.clear)
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
        
        self.output = self.create_output()
        controls_layout = self.create_controls()
        
        layout.addWidget(self.output)
        layout.addLayout(controls_layout)
        
        return layout

    def append(self, text):
        if text != None:
            self.clear_button.setEnabled(True)
            self.scroll_to_top_button.setEnabled(True)
            self.scroll_to_bottom_button.setEnabled(True)
            self.copy_button.setEnabled(True)
            self.output.append(text)
            
    def scroll_to_bottom(self):
        max_y_scroll = self.output.verticalScrollBar().maximum()
        self.output.verticalScrollBar().setValue(max_y_scroll)
        self.output.horizontalScrollBar().setValue(0)
        
    def scroll_to_top(self):
        self.output.verticalScrollBar().setValue(0)
        self.output.horizontalScrollBar().setValue(0)

    def clear(self):
        self.clear_button.setEnabled(False)
        self.scroll_to_top_button.setEnabled(False)
        self.scroll_to_bottom_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self.output.clear()
        
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output.toPlainText())
        
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
        
        # Create panels
        self.transaction_panel = TransactionPanel("Transactions", self)
        self.output_panel = OutputPanel("Output", self)
        self.operation_panel = OperationPanel("Operations", self, self.transaction_panel, self.output_panel)

        # Setup docking
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.transaction_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.operation_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.output_panel)
        self.setCentralWidget(self.operation_panel)
        
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
        self.show_popup("About", "This tool is the property of Adrien Givry.", QMessageBox.Icon.Information)
        