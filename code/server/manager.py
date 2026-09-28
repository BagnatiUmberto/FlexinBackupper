import logging
import os


class Manager():
    def __init__(self, config):
        self.config = config
        self.db_connection = None # initialized in _connect_db    
        self.formatter = logging.Formatter('%(asctime)s ---- %(levelname)s ---- %(message)s')

    def setup_logger(self, name, log_file, level=logging.INFO):
        """To setup as many loggers as you want"""
        log_folder = self.config["FOLDERS"]["logs"]
        os.makedirs(log_folder, exist_ok=True)

        handler = logging.handlers.RotatingFileHandler(os.path.join(log_folder, log_file), maxBytes=800000, backupCount=5)
        handler.setFormatter(self.formatter)

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)

        return logger
