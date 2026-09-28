import logging, logging.handlers
import os
from threading import Event
import mysql.connector
import time

class Manager():
    def __init__(self, config, stop_event : Event):
        self.config = config
        self.stop_event = stop_event

        self.registry_db_connection = None # initialized in _connect_db    
        self.formatter = logging.Formatter('%(asctime)s ---- %(levelname)s ---- %(message)s')


    def setup_logger(self, name, log_folder, log_file, level=logging.INFO):
        os.makedirs(log_folder, exist_ok=True)

        handler = logging.handlers.RotatingFileHandler(os.path.join(log_folder, log_file), maxBytes=800000, backupCount=5)
        handler.setFormatter(self.formatter)

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)

        return logger    
        
    
    def query(self, sql, params=None, dictionary = False, connection = None):
        cursor = connection.cursor(dictionary=dictionary)
        cursor.execute(sql, params or [])        
        result = cursor.fetchall()
        cursor.close()
        connection.commit()
        return result
    

    def executemany(self, sql, params_list, dictionary = False,  connection = None):
        """Esegue una query con più set di parametri
        
        es: INSERT INTO utenti (nome, email) VALUES (%s, %s)
        params_list = [("Mario", "mario@mail.com"), ("Luigi", "luigi@mail.com")]
        """
        cursor = connection.cursor(dictionary=dictionary)
        cursor.executemany(sql, params_list)        
        result = cursor.rowcount  # numero di righe inserite/modificate
        cursor.close()
        connection.commit()
        return result