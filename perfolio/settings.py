import json
import os

import qdarktheme

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy, QWidget, QTextEdit, QLineEdit, QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox, QListWidget
from perfolio.utils import Utils
        
class Setting:
    def __init__(self, instantiator, getter, setter, label, default):
        self.instantiator = instantiator
        self.getter = getter
        self.setter = setter
        self.label = label
        self.default = default
    
    def create_widget(self, id, value=None) -> QWidget:
        widget = self.instantiator()
        widget.setProperty("setting_id", id)
        self.setter(widget, self.default)
        if value:
            self.set_to_widget(widget, value)
        else:
            self.reset_widget_value(widget)
        return widget
        
    def reset_widget_value(self, widget):
        self.set_to_widget(widget, self.default)
        
    def get_from_widget(self, widget):
        return self.getter(widget)
    
    def set_to_widget(self, widget, value):
        self.setter(widget, value)
        
class SettingFactory:
    @staticmethod
    def string(label, default='', placeholder=''):     
        def instantiate():
            widget = QLineEdit()
            widget.setPlaceholderText(placeholder)
            return widget
        return Setting(instantiate, QLineEdit.text, QLineEdit.setText, label, default)
    
    @staticmethod
    def text(label, default='', placeholder=''):
        def instantiate():
            widget = QTextEdit()
            widget.setPlaceholderText(placeholder)
            widget.setFixedHeight(100)
            widget.setAcceptRichText(False)
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            return widget
        return Setting(instantiate, QTextEdit.toPlainText, QTextEdit.setPlainText, label, default)
    
    @staticmethod
    def integer(label, default=0, min=0, max=2147483647):
        def instantiate():
            widget = QSpinBox()
            widget.setMinimum(min)
            widget.setMaximum(max)
            return widget
        return Setting(instantiate, QSpinBox.value, QSpinBox.setValue, label, default)
    
    @staticmethod
    def double(label, default=0.0):
        def instantiate():
            return QDoubleSpinBox()
        return Setting(instantiate, QDoubleSpinBox.value, QDoubleSpinBox.setValue, label, default)
    
    @staticmethod
    def bool(label, default=False):
        def instantiate():
            return QCheckBox()
        return Setting(instantiate, QCheckBox.isChecked, QCheckBox.setChecked, label, default)
    
    @staticmethod
    def multilist(label, items: list[string], default=[]):
        def instantiate():
            widget = QListWidget()
            widget.addItems(items)
            widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            return widget
        
        def set(widget: QListWidget, value: list[str]):
            for row in range(widget.count()):
                item = widget.item(row)
                item.setCheckState(Qt.CheckState.Checked if item.text() in value else Qt.CheckState.Unchecked)
            
        def get(widget: QListWidget):
            return [widget.item(row).text() for row in range(widget.count()) if widget.item(row).checkState() == Qt.CheckState.Checked]
            
        return Setting(instantiate, get, set, label, default)
        
    @staticmethod
    def list(label, items: list[string], default=None):
        def instantiate():
            widget = QComboBox()
            widget.addItems(items)
            return widget
        default = items[0] if not default else default
        return Setting(instantiate, QComboBox.currentText, QComboBox.setCurrentText, label, default)
    
class AppSettings:
    settings_desc = {
        "theme": SettingFactory.list("Theme (restart to apply)", ["auto", "light", "dark"], "auto")
    }
    
    settings = {}
    
    @staticmethod
    def get(setting_id: str, force_default=False):
        use_default = force_default or not setting_id in AppSettings.settings
        if use_default:
            return AppSettings.settings_desc[setting_id].default
        else:
            return AppSettings.settings[setting_id]
    
    @staticmethod
    def set(setting_id: str, value):
        AppSettings.settings[setting_id] = value
        if setting_id == "theme":
            qdarktheme.setup_theme(value)
    
    @staticmethod
    def load_settings():
        settings_file = Utils.get_settings_file_path()
        if os.path.exists(settings_file):
            with open(settings_file, "r") as file:
                AppSettings.settings = json.load(file)

    @staticmethod
    def save_settings():
        settings_file = Utils.get_settings_file_path()
        os.makedirs(settings_file, exist_ok=True)
        with open(settings_file, "w") as file:
            json.dump(AppSettings.settings, file, indent=4)