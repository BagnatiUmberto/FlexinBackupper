import shutil
import os
import time
from datetime import datetime, timedelta
from threading import Event

from server.manager import Manager
from utils_funct import filesystem_utils as fsutil



class OldFolderDeleter(Manager):
    def __init__(self, config ):
        super().__init__(config)
        self.logger = self.setup_logger("old_folder_deleter", "old_folder_deleter.log")
        self.imgs_folder_path = self.config['IMGS']['ExtractionFolder']
        self.keep_days = int(self.config['GENERAL']['KeepDays'])


    def run(self):
        self.logger.info("OldFolderDeleter avviato.")
        while True:
            flexins_folders = []
            if os.path.isdir(self.imgs_folder_path):
                flexins_folders = os.listdir(self.imgs_folder_path)

            for flexin_folder in flexins_folders:
                flexin_folder_path = os.path.join(self.imgs_folder_path, flexin_folder)
                if not os.path.exists(flexin_folder_path):
                    self.logger.info(f"Flexin folder images non exists { flexin_folder }")
                    time.sleep(30)
                    continue

                fs_scan_funct = fsutil.walk_img_directories(flexin_folder_path)
                while True:
                    try:
                        actual_folder_info : fsutil.FolderInfo = next(fs_scan_funct)
                    except StopIteration:
                        break
                    except fsutil.RootFolderMissing:
                        break
                    except Exception as e:
                        self.logger.error(f"Exception occurred: {e}")
                        break

                    if actual_folder_info is None:
                        continue

                    if self.is_year_folder_to_delete(int(actual_folder_info['year']), self.keep_days):
                        shutil.rmtree(os.path.join(flexin_folder_path, actual_folder_info['year']))
                        self.logger.info(f"Deleted year folder: {actual_folder_info['year']}")
                        continue

                    if self.is_month_folder_to_delete(int(actual_folder_info['year']), int(actual_folder_info['month']),self.keep_days):
                        shutil.rmtree(os.path.join(flexin_folder_path, actual_folder_info['year'], actual_folder_info['month']))
                        self.logger.info(f"Deleted month folder: {actual_folder_info['month']}")
                        continue

                    if self.is_defects_folder_to_delete(actual_folder_info, self.keep_days):
                        shutil.rmtree(os.path.join(flexin_folder_path, actual_folder_info['year'], actual_folder_info['month'], actual_folder_info['folder_name']))
                        self.logger.info(f"Deleted defects imgs folder: {actual_folder_info['folder_name']}")
                        continue
            time.sleep(30)
                

    def is_year_folder_to_delete(self, year : int, keep_days:int):
        purge_date = datetime.today() - timedelta(days = keep_days)
        return True if year < purge_date.year else False


    def is_month_folder_to_delete(self, year:int, month:int, keep_days:int):
        purge_date = datetime.today() - timedelta(days = keep_days)
        if year < purge_date.year:
            return True

        if year == purge_date.year and month < purge_date.month:
            return True

        return False

    def is_defects_folder_to_delete(self, folder_info : fsutil.FolderInfo, keep_days:int):
        purge_date = datetime.today() - timedelta(days = keep_days)
        if folder_info['datetime'] > purge_date:
            return False
        else:
            return True


        



            
