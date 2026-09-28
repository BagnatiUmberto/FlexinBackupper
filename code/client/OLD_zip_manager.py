import os 
import time
from datetime import datetime
from threading import Event
import zipfile

import mysql

from client.manager import Manager
from client.paths import FLEXIN_DIR, CONFIG_DIR, LOG_DIR, ZIP_DIR

def compose_img_path(img_record : tuple) -> str:        
    img_name = img_record[0]
    year = img_record[1]
    month = img_record[2]
    day = img_record[3]
    hour = img_record[4]
    minute = img_record[5]
    folder_name = str(year)+ str(month) +str(day)+str(hour)+str(minute)
    return os.path.join(str(year), str(month), folder_name, img_name+ ".jpg")


class ZipManager(Manager):
    # ZipManager:
    # scan the db register to find unprocessed images with the function get_batch()
    # this batch is added to a set of maximum 20kb
    # When the set reaches the 20 kb threshold the files are zipped in an archive, the zipped images are checked in the DB
    # A record of the newly created zip is added to the table "zip_register"

    def __init__(self, config, stop_event : Event,id, lock):
        super().__init__(config, stop_event)
        # Setup the logger
        self.logger = self.setup_logger(f"zip_manager_{id}", LOG_DIR, f"zip_manager{id}.log")
        self.lock = lock

        # Folder where the zip files are stored
        os.makedirs(ZIP_DIR, exist_ok=True)

        # Create the "Zip in progress" dir
        self.in_progress_folder_path = os.path.join(ZIP_DIR, "In Progress")
        os.makedirs(self.in_progress_folder_path, exist_ok=True)

        # Create the "Completed zip" dir
        self.completed_folder_path = os.path.join(ZIP_DIR, "Completed")
        os.makedirs(self.completed_folder_path, exist_ok=True)

        self.imgs_folder_path = self.config["FOLDERS"]["imgs"]


    def run(self):
        self.logger.info("Zip manager started")


        # CLEANING OPERATIONS        
        # Restore the defects status that were left incomplete from the previous run
        self.clean_after_startup()

        # Get the folders that were work in progress from the previous run
        incompleted_zips = self.get_zip_in_progress_folders()


        working_folder_batch = []
        if len(incompleted_zips) != 0:
            working_folder_batch = incompleted_zips

        while(True):             

            if len(working_folder_batch) == 0:
                print("Found no folder to zip")
                time.sleep(15)
                self.move_all_zips_to_completed()
                working_folder_batch = self.get_folders_ready_to_zip()
                continue

            # Too many zip files, wait and skip to next cycle
            zip_files_num = len(os.listdir(self.in_progress_folder_path)) 
            if(zip_files_num > 300):
                self.logger.info("Too many zip files in the folder, skipping this cycle")
                time.sleep(15)
                continue

            # Loop through the folders and zip the imgs
            self.zip_folders(working_folder_batch)

            working_folder_batch = self.get_folders_ready_to_zip()
            time.sleep(1)


    ###########
    # METHODS #
    ###########

    # imgs is a list of tuple (source_path, archive_path)
    def zip_files(self, imgs: list, zip_name: str):
        '''
        Zip the imgs in the given zip file

        args:
            imgs (List[str])    : a list of the img's relative paths
            zip_name (str)      : the name of the zipfile
        '''
        zip_file = os.path.join(self.in_progress_folder_path, zip_name)
        self.logger.info(f"Zipping files to: {zip_file}")

        with zipfile.ZipFile(zip_file, 'a') as zipf:
            for img_path in imgs:
                img_abs_path = os.path.join(self.imgs_folder_path, img_path)
                zipf.write(img_abs_path, arcname=img_path)



    def zip_empty_folder(self, abs_folder_path, rel_folder_path, zip_name: str):
        '''
        Zip the empty folder

        args:
            abs_folder_path (str)   : the absolute path to the folder
            rel_folder_path (str)   : the relative path of the folder, will be recreated after the extraction
            zip_name (str)          : the name of the zipfile
        '''
        zip_file = os.path.join(self.in_progress_folder_path, zip_name)
        self.logger.info(f"Zipping empty folder to: {zip_file}")

        with zipfile.ZipFile(zip_file, 'a') as zipf:
            zipf.write(abs_folder_path, arcname=rel_folder_path)

    
    def clean_after_startup(self):
        '''
        Clean the incomplete zip and restore the database
        '''
        # Get the folder left uncompleted from the previous run
        folder_in_progress = self.get_zip_in_progress_folders()

        # Extract the folder's names from the dictionary
        folders_names = [name['folder_name'] for name in folder_in_progress]

        # Reset the defects status setting it to 0 for the defects that where zipped but not finished
        for folder in folders_names:
            self.query("UPDATE defect_imgs SET STATUS = 0 WHERE STATUS = 1 AND fk_parent_folder = %s", (folder,))

        # Delete the files in the folder

        zip_files = os.listdir(self.in_progress_folder_path)
        for el in zip_files:
            os.remove(os.path.join(self.in_progress_folder_path, el))


    def zip_folders(self, folders_records):
        '''
        Container of the functions used in the zipping folder process
        '''
        # Create a new zip file name
        zip_file_name = datetime.now().strftime("%d_%m_%Y_%H_%M_%S") + ".zip"
        for folder in folders_records:
            folder_name = folder['folder_name']

            self.mark_folder_as_zip_in_progress(folder_name)

            # Get the imgs of this folder
            imgs_to_zip = self.get_imgs_batch_to_zip(folder_name, max_size=300)

            # If the folder is empty add it and go next
            if len(imgs_to_zip) == 0:
                rel_path = folder['rel_path']
                abs_path = os.path.join(self.imgs_folder_path, rel_path)                
                self.zip_empty_folder(abs_path, rel_path, zip_file_name)

            # Loop through the defects of the folder until none left
            while len(imgs_to_zip) > 0:
                # Extract the name of the defects
                imgs_names = [(name['img_name'],) for name in imgs_to_zip]
                # Build the paths that point to the imgs
                imgs_paths = self.build_img_rel_path_from_record(imgs_to_zip)
                # Zip this files
                self.zip_files(imgs_paths, zip_file_name)
                # Mark the records in the registry
                self.mark_imgs_as_zip_in_progress(imgs_names)
                # Get the a new batch
                imgs_to_zip = self.get_imgs_batch_to_zip(folder_name, max_size=300)
                # If the size of the zip is bigger than 4MB generate a new zip file name
                zip_file_path = os.path.join(self.in_progress_folder_path, zip_file_name)
                if os.path.getsize(zip_file_path) > 4000000:
                    zip_file_name = datetime.now().strftime("%d_%m_%Y_%H_%M_%S") + ".zip"
                    zip_file_dest_path = os.path.join(self.completed_folder_path,zip_file_name)
                    # Move the zip to the completed zip folder
                    os.replace(zip_file_path, zip_file_dest_path)

            # Set the folder as zip completed
            self.query("UPDATE folders SET status = 3 WHERE folder_name = %s", (folder_name,))
            self.query("UPDATE defect_imgs SET status = 2 WHERE STATUS = 1") 


    def get_zip_in_progress_folders(self):
        return self.query("SELECT * FROM folders WHERE status = 2", dictionary= True)


    def get_imgs_batch_to_zip(self, folder_name, max_size = 250):
        '''
        Get the defectcs imgs with status 0 from the defects table
        returns:
            List([dict]) : the records retrived from the database. Are in list of dict form
        '''
        return self.query("SELECT * FROM defect_imgs WHERE fk_parent_folder = %s AND status = 0 ORDER BY img_id ASC LIMIT %s", (folder_name, max_size), dictionary=True)


    def build_img_rel_path_from_record(self, imgs_records):
        '''
        args: 
            imgs_records (List[Dict]): a list of records from defect_imgs table

        returns:
            List[str]  : A list of the relative paths of the images   
        '''

        if imgs_records is None:
            return None
        
        paths_list = []
        for img in imgs_records:
            year    = img['year']
            month   = img['month']
            folder_name = img['fk_parent_folder']
            img_name = img['img_name'] + ".jpg"

            path = os.path.join(year, month, folder_name, img_name)
            paths_list.append(path)

        return paths_list


    def mark_imgs_as_zip_in_progress(self, imgs_name_list):
        '''
        Mark the imgs in the list as zipped, status = 1

        Args:
            imgs_name_list (List[str]) : a list of imgs name to be marked as zipped

        '''
        self.executemany("UPDATE defect_imgs SET status = 1 WHERE img_name = %s", imgs_name_list)


    def get_folders_ready_to_zip(self):
        '''
        Returns:
            The folders with status 1, which all defects have been added to the DB
        '''
        return self.query("SELECT * FROM folders WHERE status = 1", dictionary= True) 


    def mark_folder_as_zip_in_progress(self, folder_name):
        self.query("UPDATE folders SET status = 2 WHERE folder_name = %s", folder_name)


    def move_all_zips_to_completed(self):
        files = os.listdir(self.in_progress_folder_path)

        for file in files:
            zip_file_path = os.path.join(self.in_progress_folder_path, file)
            zip_file_dest_path = os.path.join(self.completed_folder_path, file)
            os.replace(zip_file_path, zip_file_dest_path)
            






