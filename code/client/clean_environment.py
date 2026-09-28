import mysql.connector
import configparser
import os
from pathlib import Path


def clean(config, log_dir, zip_dir):
    # Clean logs
    for file in os.listdir(log_dir):
        os.remove(os.path.join(log_dir, file))

    # Clean zip files
    for file in os.listdir(zip_dir):
        os.remove(os.path.join(zip_dir, file))
    
    # Flush DB tables
    db_connection = mysql.connector.connect(
        host=config["DB_REGISTRY"]["host"],
        user=config["DB_REGISTRY"]["user"],
        port = int(config["DB_REGISTRY"]["port"]),
        password=config["DB_REGISTRY"]["password"],
        database=config["DB_REGISTRY"]["database"]
    )
    cursor = db_connection.cursor()
    cursor.execute("call Flush_Tables")
    db_connection.commit()
    cursor.close()
    db_connection.close()