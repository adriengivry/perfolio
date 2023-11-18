import os
import sys
        
class Utils:
    @staticmethod
    def get_appdata_path():
        return os.path.join(os.getenv('APPDATA'), 'perfolio')
    
    @staticmethod
    def get_logs_folder_path():
        return os.path.join(Utils.get_appdata_path(), 'logs')
    
    @staticmethod
    def get_bundle_dir():
        return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    @staticmethod
    def get_bundled_asset(asset_path):
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return os.path.join(Utils.get_bundle_dir(), asset_path)
        return asset_path
 