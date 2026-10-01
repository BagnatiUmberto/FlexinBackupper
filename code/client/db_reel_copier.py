'''
DBReelCopier
This module is responsible for copying the local reels, defects, recipe DBs to a remote backup DB with the same structure

The logic is the sequent:
    - Connect to the local DB
    - Connect to the remote DB
    - Check if there is an uncompleted reel copy
    - Delete from the remote DB the records that are too old based on the config file parameter "keep_days"
    - Get the Id of the latest reel copied on the remote DB
    - Get the Id of the next reel that has to be copied from the local DB
    - Copy the reel record to the remote DB
    - Extract from the local Db the defects related to this reel and copy them to the remote DB
'''

import sys, os
import time
from datetime import datetime, timedelta
from threading import Event
from pathlib import Path
import mysql.connector

from client.manager import Manager
from client.paths import LOG_DIR, DATA_DIR

class DbReelCopier(Manager):
    def __init__(self, config, stop_event : Event):
        super().__init__(config, stop_event)
        self.logger = self.setup_logger("db_reel_copier", LOG_DIR, "db_reel_copier.log")
        self.config = config
        self.stop_event = stop_event
        # Connection parameters to local Flexin DB with reels and defects
        self.local_flexin_db_conn_params = {
            'host': self.config['LOCAL_DB_REELS']['Host'],
            'user': self.config['LOCAL_DB_REELS']['User'],
            'password': self.config['LOCAL_DB_REELS']['Password'],
            'port': int(self.config['LOCAL_DB_REELS']['Port']),
            'database': self.config['LOCAL_DB_REELS']['Database']
        }

        # Connection parameters to remote Flexin DB with reels and defects
        self.remote_flexin_db_conn_params = {
            'host': self.config['REMOTE_DB_REELS']['Host'],
            'user': self.config['REMOTE_DB_REELS']['User'],
            'password': self.config['REMOTE_DB_REELS']['Password'],
            'port': int(self.config['REMOTE_DB_REELS']['Port']),
            #'database': self.config['REMOTE_DB_REELS']['Database']
        }

        # Container for the connections to the local and remote Flexin DBs
        self.local_flexin_db_connection = None
        self.remote_flexin_db_connection = None


    def run(self):
        self.logger.info("DbReelCopier started")
        while True:
            # Check the connection to the local and remote DB
            self._refresh_db_connection()

            try:
                # Create the databse              
                db_name = f"db_{self.config['GENERAL']['flexinname']}"
                self.query(f"CREATE DATABASE IF NOT EXISTS {db_name}", connection=self.remote_flexin_db_connection)
                self.remote_flexin_db_conn_params["database"] = db_name
                self._refresh_db_connection()

                # Create the tables
                sql_tables = ["tablebob", "tabledif", "tablericette", "tablespeed", "tablewidth"]

                for el in sql_tables:
                    query_string = self.get_table_create(el)[0][1]                   
                    query_string = query_string.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS ")
                    query_string =  query_string.replace("AUTO_INCREMENT", "", 1)
                    query_string = query_string.replace("\n","")
                    self.query(query_string, connection=self.remote_flexin_db_connection)

                self.logger.info("Inserting recipies")
                self.insert_recipies()
                self.insert_table_speed()
                self.insert_table_width()

                last_copied_reel = None

                # Delete file older than keepdays in config
                self._delete_older_records(self.remote_flexin_db_connection)

                # Get the reel currently in production, this must be skipped
                reel_in_production = self.get_max_element("tablebob", self.local_flexin_db_connection)

                #print("max reel: " + str(reel_in_production))
                if reel_in_production is None:
                    self.logger.info("No reel found on local DB")
                    time.sleep(60)
                    continue   

                # Get the latest reel loaded on the remote connection
                last_copied_reel = self.get_max_element("tablebob", self.remote_flexin_db_connection)                    

                # Get reels and load
                reels_to_copy = self._get_reels_to_copy(self.local_flexin_db_connection, last_copied_reel, reel_in_production)

                if reels_to_copy is not None and len(reels_to_copy) != 0:
                    col_num = self.get_columns_number(self.local_flexin_db_connection, "tablebob")
                    placeholders = ", ".join(["%s"] * col_num)
                    self.executemany(f"INSERT IGNORE INTO tablebob VALUES ({placeholders})", reels_to_copy, connection=self.remote_flexin_db_connection)

                # Get defects and load
                last_copied_defect = self.get_max_element("tabledif", self.remote_flexin_db_connection)

                defects_to_copy = self._get_defects_to_copy(self.local_flexin_db_connection, last_copied_defect, reel_in_production)

                if defects_to_copy is not None and len(defects_to_copy) != 0:
                    col_num = self.get_columns_number(self.local_flexin_db_connection, "tabledif")
                    placeholders = ", ".join(["%s"] * col_num)
                    self.executemany(f"INSERT IGNORE INTO tabledif VALUES ({placeholders})", defects_to_copy, connection=self.remote_flexin_db_connection)

                
                if len(defects_to_copy) == 0 and len(reels_to_copy) == 0:
                    print("\r\n[DB COPIER] - No reels to copy found, going to sleep, see you in 100 sec...")
                    time.sleep(100)  # Simulate work being done

            except mysql.connector.Error as err:
                self.logger.error(f"MySql error: {err}")
                if self.remote_flexin_db_connection is not None:
                    try:
                        self.remote_flexin_db_connection.disconnect()
                    except Exception:
                        pass
                self.remote_flexin_db_connection = None

                if self.local_flexin_db_connection is not None:
                    try:
                        self.local_flexin_db_connection.disconnect()
                    except Exception:
                        pass

                self.local_flexin_db_connection = None
                time.sleep(10)                
                continue
    
    '''
    TIME FUNCTIONS
    '''
    # Returns the current date-time minus timedelta from config in the format YYYYMMDDHHMM
    def calc_date_based_on_keep_days_YYYYMMDDHHMM(self):
        keep_days = int(self.config['GENERAL']['keepdays'])
        date = datetime.today() - timedelta(days=keep_days)
        return date.strftime("%Y%m%d%H%M")

    '''
    DB CONNECTION FUNCTIONS
    '''
    def connect_db(self, conn_params, delay=10):
        attempt = 0

        while not self.stop_event.is_set():
            attempt += 1

            try:
                self.logger.info(
                    f"Trying to connect to DB "
                    f"{conn_params['host']}:{conn_params['port']} "
                    f"(attempt {attempt})"
                )

                connection = mysql.connector.connect(**conn_params)
                connection.autocommit = False

                self.logger.info("DB connection established")

                return connection

            except mysql.connector.Error as e:
                self.logger.error(
                    f"DB connection failed: {e}. "
                    f"Retrying in {delay}s..."
                )

                self.stop_event.wait(delay)

    
    # Check the status of the DB connection, if missing try to reconnect
    def _refresh_db_connection(self):
        if self.local_flexin_db_connection is None:
            self.local_flexin_db_connection = self.connect_db(self.local_flexin_db_conn_params)
        else:
            self.local_flexin_db_connection.disconnect()
            self.local_flexin_db_connection = self.connect_db(self.local_flexin_db_conn_params)


        if self.remote_flexin_db_connection is None:
            self.remote_flexin_db_connection = self.connect_db(self.remote_flexin_db_conn_params)
        else:
            self.remote_flexin_db_connection.disconnect()
            self.remote_flexin_db_connection = self.connect_db(self.remote_flexin_db_conn_params)
            
    

    '''
    CRUD FUNCTIONS
    '''

    def get_max_element(self, table_name, connection) -> dict:
        result = self.query(f"SELECT * FROM {table_name} WHERE ID = (SELECT MAX(ID) from {table_name})", dictionary = True, connection=connection)
        return result[0] if len(result) > 0 else None


    def _get_max_id(self, connection, table_name):
        result =  self.query(f"SELECT MAX(id) FROM {table_name}", connection=connection)[0]
        return result[0] if len(result) > 0 else None

    def _get_reels_to_copy(self, connection, last_copied, reel_in_production):
        last_copied_id = -1

        if last_copied is not None:
            last_copied_id = last_copied['ID']

        if reel_in_production is None:
            return None

        in_work_id = reel_in_production['ID']

        threshold_date = self.calc_date_based_on_keep_days_YYYYMMDDHHMM()
        result = self.query("SELECT * FROM tablebob WHERE  %s < ID  AND ID < %s AND IDENTDIF > %s ORDER BY ID ASC LIMIT 250", 
                       (last_copied_id, in_work_id, threshold_date), connection=connection)
        return result


    def _get_defects_to_copy(self, connection, last_copied_defect, reel_in_production):
        last_copied_defect_id = -1 if last_copied_defect is None else last_copied_defect['ID']
        threshold_date = self.calc_date_based_on_keep_days_YYYYMMDDHHMM()
        reel_ident = reel_in_production['IDENTDIF']
        result = self.query("SELECT * FROM tabledif WHERE id > %s AND IDENTDIF > %s AND IDENTDIF < %s ORDER BY ID ASC LIMIT 2500", 
                       (last_copied_defect_id, threshold_date, reel_ident),
                       connection=connection)
        return result


    def _delete_older_records(self, connection):
        date_on_keepdays = self.calc_date_based_on_keep_days_YYYYMMDDHHMM()
        # Delete reel records
        cursor = connection.cursor()
        delete_query = "DELETE FROM tablebob where identdif <= %s"
        cursor.execute(delete_query, (date_on_keepdays,))
        connection.commit()
        cursor.close()

        # Delete defect records
        cursor = connection.cursor()
        delete_query = "DELETE FROM tabledif where identdif <= %s"
        cursor.execute(delete_query, (date_on_keepdays,))
        connection.commit()
        cursor.close()


    def get_columns_number(self, connection, table_name):
        '''
        Get the number of columns of the table

        return (int):
            the number of columns in the DB            
        '''
        cursor = connection.cursor()
        query = f"SHOW COLUMNS FROM {table_name};"
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return len(result)


    def insert_recipies(self):
        self.query("DELETE from tablericette", connection=self.remote_flexin_db_connection)
        
        result = self.query("SELECT * from tablericette", connection=self.local_flexin_db_connection)
        col_num = self.get_columns_number(self.local_flexin_db_connection, "tablericette")
        placeholders = ", ".join(["%s"] * col_num)

        for record in result:
            query = f"INSERT IGNORE INTO tablericette VALUES ({placeholders}) "
            self.query(query, params= record,  connection=self.remote_flexin_db_connection)
        self.logger.info(f"Inserted {str(len(result))} recipes")



    def insert_table_speed(self):
        id_last_loaded_remote = self._get_max_id(self.remote_flexin_db_connection, "tablespeed")

        if id_last_loaded_remote is None:
            id_last_loaded_remote = -1

        id_last_loaded_local = self._get_max_id(self.local_flexin_db_connection, "tablespeed")

        if id_last_loaded_local is None:
            self.logger.info("No records found on local tablespeed")
            return

        if id_last_loaded_remote < id_last_loaded_local:
            # Get the records to load
            results = self.query("SELECT * FROM tablespeed WHERE id > %s ORDER BY ID ASC LIMIT 2500", (id_last_loaded_remote,), connection = self.local_flexin_db_connection)
            if not results or len(results) == 0:
                self.logger.info("No new records to load found on tablespeed")
                return
            col_num = self.get_columns_number(self.local_flexin_db_connection, "tablespeed")
            placeholders = ", ".join(["%s"] * col_num)
            self.executemany(f"INSERT IGNORE INTO tablespeed VALUES ({placeholders})", results, connection=self.remote_flexin_db_connection)
            self.logger.info(f"Inserted records in tablespeed from {str(id_last_loaded_remote)} to {str(id_last_loaded_local)}")


    def insert_table_width(self):
        id_last_loaded_remote = self._get_max_id(self.remote_flexin_db_connection, "tablewidth")
        if id_last_loaded_remote is None:
            id_last_loaded_remote = -1

        id_last_loaded_local = self._get_max_id(self.local_flexin_db_connection, "tablewidth")
        if id_last_loaded_local is None:
            self.logger.info("No records found on local tablewidth")
            return

        if id_last_loaded_remote < id_last_loaded_local:
            # Get the records to load
            results = self.query("SELECT * FROM tablewidth WHERE id > %s ORDER BY ID ASC LIMIT 2500", (id_last_loaded_remote,), connection = self.local_flexin_db_connection)
            if not results or len(results) == 0:
                self.logger.info("No new records to load found on tablewidth")
                return
            col_num = self.get_columns_number(self.local_flexin_db_connection, "tablewidth")
            placeholders = ", ".join(["%s"] * col_num)
            self.executemany(f"INSERT IGNORE INTO tablewidth VALUES ({placeholders})", results, connection=self.remote_flexin_db_connection)
            self.logger.info(f"Inserted records in tablewidth from {str(id_last_loaded_remote)} to {str(id_last_loaded_local)}")


    def get_table_create(self, table_name):
        result = self.query(f"SHOW CREATE TABLE {table_name}", connection = self.local_flexin_db_connection)
        return result








