"""
File Transfer Server
- Trasferimento a chunk con checksum CRC32 per ogni chunk
- Rollback automatico in caso di errore o corruzione
- Supporto ripresa trasferimento (resume)
- Verifica integrità finale SHA-256
"""

import configparser
import logging
import os

from pathlib import Path
import threading
import time
from server.extractor_manager import ExtractorManager
from server.tcpserver_manager import TCPServerManager
from server.folder_deletion_manager import OldFolderDeleter
from server.paths import APPDATA_DIR, FLEXIN_DIR, CONFIG_DIR, LOG_DIR, ZIP_DIR, TEMP_TRANSFERS_DIR, RECEIVED_FILES_DIR, EXTRACTED_DIR


def main():

    os.makedirs(FLEXIN_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(ZIP_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    # Create zip subfolders
    os.makedirs(TEMP_TRANSFERS_DIR, exist_ok=True)
    os.makedirs(RECEIVED_FILES_DIR, exist_ok=True)
    os.makedirs(EXTRACTED_DIR, exist_ok=True)


    if not Path(os.path.join(CONFIG_DIR, "config.ini")).exists():
        print("config.ini not found, creating a default one...")
        write_default_config()
        print("Default config.ini created, please edit it and restart the application")
        print(f"Config file path: {os.path.join(CONFIG_DIR, 'config.ini')}")
        input("Press Enter to exit...")
        return
    
    print("Starting server main...")
    config = configparser.ConfigParser()
    config.read(os.path.join(CONFIG_DIR, "config.ini"))

    tcpserver_manager = TCPServerManager(config)
    tcpserver_manager_thread = threading.Thread(target=tcpserver_manager.run, daemon=True)
    tcpserver_manager_thread.start()

    extractor_manager = ExtractorManager(config)
    extractor_manager_thread = threading.Thread(target=extractor_manager.run, daemon=True)
    extractor_manager_thread.start()

    folder_deleter_manager = OldFolderDeleter(config)
    folder_deleter_manager_thread = threading.Thread(target=folder_deleter_manager.run, daemon=True)
    folder_deleter_manager_thread.start()


    while True:
        time.sleep(1)  # Main thread can perform other tasks or just sleep


def write_default_config():
    default_config = configparser.ConfigParser()

    default_config['GENERAL'] = {
        'Host'  : '',
        'Port'  : '50007',
        'ExtractZips' : 'True',
        'KeepDays' : '365'
    }

    default_config['IMGS'] = {
        'ExtractionFolder'  : EXTRACTED_DIR,
    }

    default_config['FOLDERS'] = {
        'Config': CONFIG_DIR,
        'Zips'  : ZIP_DIR,
        'Logs'  : LOG_DIR
    }

    with open(os.path.join(CONFIG_DIR, "config.ini"), 'w') as configfile:
        default_config.write(configfile)


if __name__ == "__main__":
    main()