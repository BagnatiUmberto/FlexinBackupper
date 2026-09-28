import configparser
import os
from threading import Event
import time

from client.manager import Manager
from client.paths import FLEXIN_DIR, CONFIG_DIR, LOG_DIR, ZIP_DIR

class CleanerManager(Manager):
    def __init__(self, config, stop_event : Event):
        super().__init__(config, stop_event)
        self.logger = self.setup_logger("cleaner_manager", LOG_DIR, "cleaner_manager.log")
        
    def run(self):
        self.logger.info("Cleaner manager started")
        while True:        
            try:
                # Delete completed zip files
                completed_zips = self.get_sent_zips()
                if completed_zips:
                    for zip_name in completed_zips:
                        zip_path = os.path.join(ZIP_DIR, zip_name)
                        if os.path.exists(zip_path):
                            try:
                                os.remove(zip_path)
                                self.mark_deleted(zip_name)                     
                                self.logger.info(f"Deleted zip file: {zip_path}")
                            except OSError as e:
                                self.logger.error(f"Error deleting zip file {zip_path}: {e}")
                        else:
                            self.logger.warning(f"Zip file not found for deletion: {zip_path}")
                else:
                    self.logger.info("No completed zip files to delete")
           
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Fatal error in cleaner manager {e}")
                self.stop_event.set()  # avvisa il padre


    def get_sent_zips(self):
        """
        Retrive zip files from the database that have been already sent (status = 1)
        """
        self.logger.info("Getting sent zip files")
        result = self.query("SELECT zip_name FROM zip_registry WHERE status = 1")
        
        if result:
           return [row[0] for row in result]
        return None

        
    def mark_deleted(self, zip_name: str):
        """
        Update the zip table marking the zip as deleted (status = 2)
        """
        self.logger.info(f'Marking zip as deleted (status 2): {zip_name}')
        self.query("UPDATE zip_registry SET status = '2' WHERE zip_name = %s", (zip_name,))


