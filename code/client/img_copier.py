import os
import json
import shutil
import random
from datetime import datetime
import time
from datetime import timedelta
import sqlite3
from typing import TypedDict, List
import zipfile
 
from client.manager import Manager
from utils_funct import filesystem_utils as fsutil
from client.paths import LOG_DIR, DATA_DIR, FLEXIN_DIR, CONFIG_DIR, ZIP_DIR

# Per rendere il software più robusto si potrebbe azzerare il journal ogni tot esecuzioni 
# così da fare ripartire il sistema e includere eventuali immagini mancanti

# Class definition for returned dictionaries
class JournalInfo(TypedDict):
    img_name    : str
    folder      : str
    year        : str
    month       : str
    day         : str
    hour        : str
    minute      : str
    img_idx     : int
    last_zip    : str


####################
# MAIN CLASS
####################
class ImgCopierManager(Manager):
    def __init__(self, config, stop_event):
        super().__init__(config, stop_event)
        # Setup the logger
        self.logger = self.setup_logger("img_copier", LOG_DIR, "img_copier.log")

        # Setup constants
        self.max_zip_size_byte = int (self.config['GENERAL']['MaxZipeSizeByte'])
        self.keep_days_config = int(self.config['GENERAL']['KeepDays'])
        self.file_ext = self.config['GENERAL']['FileExtension']
        self.pause_time = int(self.config['GENERAL']['PauseTime'])

        # IMGS folder
        self.imgs_folder_path = self.config["FOLDERS"]["imgs"]

        # ZIP folder
        self.in_progress_zip_path = os.path.join(ZIP_DIR, "In Progress")
        self.completed_zip_path = os.path.join(ZIP_DIR, "Completed")


        # Check if "completed.ini" exists
        self.journal_path = os.path.join(DATA_DIR, "last_completed.json")
        self.errors_journal_path = os.path.join(DATA_DIR, "errors.txt")
        
            


    def run(self):
        # Folder where the zip files are stored
        os.makedirs(ZIP_DIR, exist_ok=True)
        

        # Delete the folder that could be dirty from the previous run
        if os.path.exists(self.in_progress_zip_path):
            shutil.rmtree(self.in_progress_zip_path)

        # Create the "Zip in progress" dir
        os.makedirs(self.in_progress_zip_path, exist_ok=True)

        # Create the "Completed zip" dir
        os.makedirs(self.completed_zip_path, exist_ok=True)


        # Create a new zip file name
        zip_file_name = self.get_new_zip_name()
        final_zip_path = os.path.join(self.completed_zip_path, zip_file_name)
        temp_zip_path = os.path.join(self.in_progress_zip_path, zip_file_name + ".tmp")


        self.create_sqlite_db()
        

        while True:
            
            last_folder_info : fsutil.FolderInfo = fsutil.fs_get_last_folder(self.imgs_folder_path)

            scan_func = fsutil.walk_img_directories(self.imgs_folder_path)
            temp_img_list = []

            while True:
                try:
                    actual_folder_info : fsutil.FolderInfo = next(scan_func)
                    self.logger.info(f"Next folder: {actual_folder_info['folder_name']}")
                except StopIteration:
                    break


                if not actual_folder_info:
                    continue

                if self.is_folder_expired(actual_folder_info):
                    self.logger.info(f"Skipping folder {actual_folder_info['folder_name']}: older than retention window ({self.keep_days_config} days), not copied")
                    continue

                
                folder_path = os.path.join(self.imgs_folder_path, actual_folder_info['rel_path'])
                

                for img in os.listdir(folder_path):
                    
                    if self.img_exists(img):
                        print(f"\rImage {img} skipped", end="", flush=True)
                        continue                  
                    img_abs_path = os.path.join(folder_path, img)
                    img_rel_path = os.path.join(actual_folder_info['rel_path'], img)

                    try:
                        with zipfile.ZipFile(temp_zip_path, 'a') as zipf:                                
                            zipf.write(img_abs_path, arcname=img_rel_path)
                        temp_img_list.append((img,))
                        print(f"\rImage {img} added to the zip", end="", flush=True)
                        self.logger.info(f"Image {img} added to the zip")
                            
                    except:
                        self.logger.error(f"Error during the zip of the file: {img}")
                        continue

                    time.sleep(0.001)               


                    if os.path.exists(temp_zip_path):
                        zip_size = os.path.getsize(temp_zip_path)
                        
                        # Max zip size reached: rotate the zip
                        if zip_size > self.max_zip_size_byte:                    
                            try:
                                os.replace(temp_zip_path, final_zip_path)
                            except:
                                os.remove(temp_zip_path)

                            if len(temp_img_list) > 0:
                                self.write_img_db(temp_img_list)
                            temp_img_list = []

                            zip_file_name = self.get_new_zip_name()
                            final_zip_path = os.path.join(self.completed_zip_path, zip_file_name)
                            temp_zip_path = os.path.join(self.in_progress_zip_path, zip_file_name + ".tmp")



                if actual_folder_info['folder_name'] == last_folder_info['folder_name']:
                    if os.path.exists(temp_zip_path):
                        try:
                            os.replace(temp_zip_path, final_zip_path)
                        except:
                            os.remove(temp_zip_path)

                        if len(temp_img_list) > 0:
                            self.write_img_db(temp_img_list)
                        temp_img_list = []

                        zip_file_name = self.get_new_zip_name()
                        final_zip_path = os.path.join(self.completed_zip_path, zip_file_name)
                        temp_zip_path = os.path.join(self.in_progress_zip_path, zip_file_name + ".tmp")


            self.logger.info("End of scan fs")
            for i in range(self.pause_time):
                print(f"\rNew cycle starting in {self.pause_time - i} seconds", end="", flush=True)
                time.sleep(1)


    ################
    # ZIP OPERATIONS
    ################
    def get_new_zip_name(self):
        return datetime.now().strftime("%d_%m_%Y_%H_%M_%S_%f") + ".zip"

    

    def is_folder_expired(self, folder_info: fsutil.FolderInfo) -> bool:
        '''
        Return True if the folder's datetime is older than the retention
        window configured via KeepDays (self.keep_days_config).
 
        Folders older than "now - keep_days_config days" are considered
        expired and must no longer be copied into a zip.
        '''
        cutoff_datetime = datetime.now() - timedelta(days=self.keep_days_config)
        return folder_info['datetime'] < cutoff_datetime



    ###############
    # FS OPERATIONS
    ###############
    def write_journal(self, img_name, idx, zip_file_name):
        img_info : fsutil.ImageInfo = fsutil.extract_img_info(img_name)
        with open(self.journal_path + ".tmp", 'w') as file:
            data : JournalInfo = {
                'img_name'      : img_name,
                'folder'        : img_info['parent_folder'],
                'year'          : img_info['year'],
                'month'         : img_info['month'],
                'day'           : img_info['day'],
                'hour'          : img_info['hour'],
                'minute'        : img_info['minute'],
                'img_idx'       : idx,
                'last_zip'      : zip_file_name
            }
            json_str = json.dumps(data, indent=4)
            file.write(json_str)
            file.flush()
            os.fsync(file.fileno())
        os.replace(self.journal_path + ".tmp", self.journal_path)



    def create_imgs_list(self, folder_info : fsutil.FolderInfo, last_folder_name, last_img_idx) -> List[str]:
        '''
        Returns a list containing the names of the imgs that have to be zipped based on the last_folder_name and last_img_idx
        Args:
            last_folder_name(str): the name of the last folder zipped
            last_img_idx(int): the index of the last image zipped from the last folder, the idx is obtained by sorting the images

        Returns(List[str]):
            the list of images
        '''
        folder_name = folder_info['folder_name']
        imgs_list = []
        folder_abs_path = os.path.join(self.imgs_folder_path, folder_info['rel_path'])
        if not os.path.isdir(folder_abs_path):
            raise fsutil.RootFolderMissing(f"Folder is missing: {folder_abs_path}")

        imgs_list = sorted(os.listdir(folder_abs_path))
        # If is the next folder after the one we last added to the
        # in-progress zip, take all its images
        if folder_name > last_folder_name:
            return imgs_list    

        if folder_name == last_folder_name:
            return imgs_list[last_img_idx:]

        return imgs_list
        


    def write_missing(self, abs_img_path : str, rel_img_path : str):
        with open(self.errors_journal_path,  'a') as file:
            file.write(f"{abs_img_path}-{rel_img_path}\n")



    def zip_missing(self, zip_file):
        if not os.path.exists(self.errors_journal_path):
            return
        with open(self.errors_journal_path,  'r') as file:
            for line in file:
                with zipfile.ZipFile(zip_file, 'a') as zipf:
                    stripped = line.strip()
                    abs_path = stripped.split("-")[0]              
                    rel_path = stripped.split("-")[1]
                    zipf.write(abs_path, arcname=rel_path)


    def create_sqlite_db(self):
        conn = sqlite3.connect(os.path.join(DATA_DIR, "register.db"))  # Creates a new database file if it doesn’t exist
        cursor_obj = conn.cursor()

        cursor_obj.execute("CREATE TABLE IF NOT EXISTS register (" \
        "path varchar(255) PRIMARY KEY" \
        ");")
        conn.commit()
        conn.close()
        return conn


    def img_exists(self, img_name) -> bool:
        conn = sqlite3.connect(os.path.join(DATA_DIR, "register.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT * from register where path = ?", (img_name, ))
        result = cursor.fetchall()
        conn.commit()
        conn.close()
        return True if len(result) > 0 else False


    def write_img_db(self, imgs_list) -> bool:
        conn = sqlite3.connect(os.path.join(DATA_DIR, "register.db"))
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO register VALUES (?)", imgs_list)
        conn.commit()
        conn.close()





