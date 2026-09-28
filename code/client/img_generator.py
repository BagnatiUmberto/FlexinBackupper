import os
import shutil
import time
from datetime import datetime

from pathlib import Path

from paths import FLEXIN_DIR, CONFIG_DIR, LOG_DIR, ZIP_DIR, DATA_DIR

if __name__=="__main__":
    imgs_dir = "C:\\Users\\bagnati.umberto\\Documents\\Projects\\Scambio Dati DB Flexin\\misc\\Img_copy"
    reference_img = "C:\\Users\\bagnati.umberto\\Documents\\Projects\\Scambio Dati DB Flexin\\misc\\reference_img.jpg"
    previous_time = datetime.now()

    while True:
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d%H%M")

        year        =   timestamp_str[0:4]
        month       =   timestamp_str[4:6]
        day         =   timestamp_str[6:8]
        hour        =   timestamp_str[8:10]
        minute      =   timestamp_str[10:12]

        year_path = os.path.join(imgs_dir, year)
        month_path = os.path.join(year_path, month)
        day_path = os.path.join(month_path, timestamp_str)

        os.makedirs(year_path, exist_ok=True)
        os.makedirs(month_path, exist_ok=True)
        os.makedirs(day_path, exist_ok=True)

        for i in range(1000):
            shutil.copy(reference_img, os.path.join(day_path, f"{timestamp_str}-{str(i)}.jpg" ))

        time_dif = datetime.now() - previous_time

        while time_dif.total_seconds() < 60:
            time.sleep(1)
            time_dif = datetime.now() - previous_time

        previous_time = datetime.now()


