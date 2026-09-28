'''
In questa nuova versione del client verranno appostate le seguenti modifiche:
- L'interfaccia grafica verrà rimossa
- Il databse con il registro delle immagini caricate non sarà più locale al client, ma verrà spostato sul server
- Le operazione verranno gestite da dei "worker", ognuno in un proprio thread, e orchestrati da un "manager"
- I worker avranno un'interfaccia simile a quella delle FB dei PLC, con segnali di start, stop, error, done, busy
- Il manager avrà il compito di gestire i worker, assegnare loro i task, e monitorare il loro stato
- I worker saranno i seguenti: registry_loader, zipper, sender, deleter

registry_loader: si occuperà di caricare sul registro/db le nuove immagini prodotte dal flexin
zipper: si occuperà di comprimere le immagini in un archivio zip
sender: si occuperà di inviare le immagini al server tramite protocollo TCP
deleter: si occuperà di eliminare le immagini dal client secondo le opportune politiche di retention
'''
import configparser
import os
from pathlib import Path
import threading

from client.paths import FLEXIN_DIR, CONFIG_DIR, LOG_DIR, ZIP_DIR, DATA_DIR
from client.clean_environment import clean
from client.tcp_manager import tcp_client_manager
from client.img_copier import ImgCopierManager
from client.db_reel_copier import DbReelCopier


def main():
    os.makedirs(FLEXIN_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(ZIP_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)


    if not Path(os.path.join(CONFIG_DIR, "config.ini")).exists():
        print("config.ini not found, creating a default one...")
        write_default_config()
        print("Default config.ini created, please edit it and restart the application")
        print(f"Config file path: {os.path.join(CONFIG_DIR, 'config.ini')}")
        input("Press Enter to exit...")
        return
        
        
    print("Client started...")
    config = configparser.ConfigParser()
    try:
        config.read(os.path.join(CONFIG_DIR, "config.ini"))
    except Exception as e:
        print(f"Error reading config file: {e}")
        return

    stop_event = threading.Event()

    img_copier = ImgCopierManager(config, stop_event)
    img_copier_thread = threading.Thread(target=img_copier.run, daemon=True)
    img_copier_thread.start()

    db_copier = DbReelCopier(config, stop_event)
    db_copier_thread = threading.Thread(target=db_copier.run, daemon=True)
    db_copier_thread.start()    
    

    tcp_manager = tcp_client_manager(config, stop_event)
    tcp_manager_thread = threading.Thread(target=tcp_manager.run, daemon=True)
    tcp_manager_thread.start()
    
    try:
        while not stop_event.is_set():
            stop_event.wait(timeout=1)
    except KeyboardInterrupt:
        print("\nCtrl+C ricevuto, fermo i worker...")
        stop_event.set()
        raise  # propaga al main.py

    
def write_default_config():
    default_config = configparser.ConfigParser()

    default_config['GENERAL'] = {
        'FlexinName'    : 'FlexinName',
        'KeepDays' : '365',
        'FileExtension' : 'jpg',
        'MaxZipeSizeByte' : '20000',
        'PauseTime' : '10'
    }

    default_config['SERVER_CONN'] = {
        'ServerIP'    : '127.0.0.1',
        'Port'  : '50007'
    }


    default_config['LOCAL_DB_REELS'] = {
        'Host'  : 'localhost',
        'User'  : 'root',
        'Password'  : 'root',
        'Port'  : '3306',
        'Database'  : ''
    }

    default_config['REMOTE_DB_REELS'] = {
        'Host'  : '192.168.1.100',
        'User'  : 'root',
        'Password'  : 'root',
        'Port'  : '3306',
        'Database'  : 'flexindb'
    }

    default_config['FOLDERS'] = {
        'Imgs'  : "E:/StoricSql/dbaseImm"
    }

    with open(os.path.join(CONFIG_DIR, "config.ini"), 'w') as configfile:
        default_config.write(configfile)


if __name__ == "__main__":
    main()



