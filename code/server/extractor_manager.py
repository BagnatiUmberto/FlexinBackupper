import os
import shutil
import time
from pathlib import Path

from server.manager import Manager
from server.paths import APPDATA_DIR, FLEXIN_DIR, CONFIG_DIR, LOG_DIR, ZIP_DIR, TEMP_TRANSFERS_DIR, RECEIVED_FILES_DIR, EXTRACTED_DIR

class ExtractorManager(Manager):
    def __init__(self, config):
        super().__init__(config)
        print("Initializing ExtractorManager...")
        self.logger = self.setup_logger("extractor_manager", "extractor_manager.log")
        self.logger.info("ExtractorManager initialized")
        self.extraction_path = Path(self.config["IMGS"]["ExtractionFolder"])
        os.makedirs(self.extraction_path, exist_ok=True)


    def run(self):
        self.logger.info("ExtractorManager started")
        

        while True:
            if not os.path.exists(RECEIVED_FILES_DIR):
                time.sleep(10)
                continue
            flexin_folders = os.listdir(RECEIVED_FILES_DIR)
            for flexin_folder in flexin_folders:
                if os.path.isdir(os.path.join(RECEIVED_FILES_DIR, flexin_folder)):
                    for zip_file in os.listdir(os.path.join(RECEIVED_FILES_DIR, flexin_folder)):
                        zip_file_path = os.path.join(RECEIVED_FILES_DIR, flexin_folder, zip_file)
                        zip_extract_path = os.path.join(self.extraction_path, flexin_folder)
                        os.makedirs(zip_extract_path, exist_ok=True)
                        if os.path.isfile(zip_file_path) and zip_file.endswith(".zip"):
                            self.logger.info(f"Started extraction of {zip_extract_path}\n")
                            try:
                                shutil.unpack_archive(zip_file_path, zip_extract_path)
                                self.logger.info(f"Extracted zip file: {zip_file} for flexin {flexin_folder} \n")
                            except:
                                self.logger.error(f"Error during the extraction of the zip {zip_file} for flexin {flexin_folder}\n")

                            try:
                                os.remove(zip_file_path)  # Remove the zip file after extraction
                                self.logger.info(f"Removed zip file: {zip_file} for flexin {flexin_folder}\n")
                            except:
                                self.logger.error(f"Error in removing the zip {zip_file} for flexin {flexin_folder}\n")

                time.sleep(10)  # Sleep to avoid busy waiting
        



       