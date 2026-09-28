import os

# %APPDATA%
APPDATA_DIR = os.getenv('LOCALAPPDATA')
# %APPDATA%/FlexinBackupper
FLEXIN_DIR = os.path.join(APPDATA_DIR, "FlexinBackupper", "client")
# %APPDATA%/FlexinBackupper/client/config
CONFIG_DIR = os.path.join(FLEXIN_DIR, "CONFIG")
# %APPDATA%/FlexinBackupper/client/logs
LOG_DIR = os.path.join(FLEXIN_DIR, "LOGS")
# %APPDATA%/FlexinBackupper/client/zips
ZIP_DIR = os.path.join(FLEXIN_DIR, "ZIPS")
# %APPDATA%/FlexinBackupper/client/data
DATA_DIR = os.path.join(FLEXIN_DIR, "DATA")
