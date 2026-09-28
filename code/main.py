# main.py
import configparser
import os
import sys

from server import server_main

from client.paths import FLEXIN_DIR, CONFIG_DIR, LOG_DIR, ZIP_DIR, DATA_DIR, APPDATA_DIR
from client.clean_environment import clean
from client import client_main
from test import check_extraction

if __name__ == '__main__':
    mode = ""    
    config = configparser.ConfigParser()
    # Print the logo
    basedir = os.path.dirname(__file__)
    logo_path = os.path.join(basedir, "assets", "imgs", "logo ASCII.txt")
    if os.path.exists(logo_path):
        with open(logo_path) as file:
            content = file.read()
            print(content)

    print("\n\n")
    print(f"Configuration file can be found at: { CONFIG_DIR }")
    print("\n\n")

    if len(sys.argv[1:]) == 0:
        user_input = input("Enter mode (server/client/clean), if no config file was found a default one will be created: ").strip().lower()
        mode = user_input if user_input in ['server', 'client', 'clean', 'test'] else None
    else:
        mode = sys.argv[1]
    
    if mode == 'clean':
        clean(config, LOG_DIR, ZIP_DIR)
        print("Environment cleaned")

    elif mode == 'server':
        server_main.main()

    elif mode == 'client':        
        client_main.main()

    elif mode == 'test':        
            check_extraction.main()

    else:
        print("Uso: python main.py server|client")