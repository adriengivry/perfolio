import os
import sys
import json

from datetime import datetime
from dateutil import parser

class Utils:
    @staticmethod
    def get_appdata_path():
        return os.path.join(os.getenv('APPDATA'), 'perfolio')
    
    @staticmethod
    def get_logs_folder_path():
        return os.path.join(Utils.get_appdata_path(), 'logs')
    
    @staticmethod
    def get_settings_file_path():
        return os.path.join(Utils.get_appdata_path(), "settings.json")
    
    @staticmethod
    def get_user_file_path():
        return os.path.join(Utils.get_appdata_path(), "user.json")
    
    @staticmethod
    def store_last_opened_portfolio(portfolio_file_path: str):
        user_file = Utils.get_user_file_path()
        data = {'last_portfolio_opened': portfolio_file_path}
        with open(user_file, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    @staticmethod
    def retrieve_last_opened_portfolio():
        user_file = Utils.get_user_file_path()
        if os.path.exists(user_file):
            with open(user_file, 'r') as json_file:
                try:
                    data = json.load(json_file)
                    last_portfolio_opened = data.get('last_portfolio_opened')
                    if last_portfolio_opened and os.path.exists(last_portfolio_opened):
                        return last_portfolio_opened
                    else:
                        return None  # Return None if last_cwd is invalid or directory doesn't exist
                except json.JSONDecodeError:
                    return None  # Return None if there's an issue decoding JSON
        else:
            return None  # Return None if JSON file doesn't exist
    
    @staticmethod
    def get_supported_date_formats():
        return ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"]
    
    @staticmethod
    def convert_date_format(date, format="%Y-%m-%d"):
        try:
            parsed_date = parser.parse(date)
            return parsed_date.strftime(format)
        except:
            return None
 