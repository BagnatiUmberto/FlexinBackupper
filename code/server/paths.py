import os

# %APPDATA%
APPDATA_DIR = os.getenv('LOCALAPPDATA')
# %APPDATA%/FlexinBackupper
FLEXIN_DIR = os.path.join(APPDATA_DIR, "FlexinBackupper", "server")
# %APPDATA%/FlexinBackupper/server/config
CONFIG_DIR = os.path.join(FLEXIN_DIR, "CONFIG")
# %APPDATA%/FlexinBackupper/server/logs
LOG_DIR = os.path.join(FLEXIN_DIR, "LOGS")
# %APPDATA%/FlexinBackupper/server/zips
ZIP_DIR = os.path.join(FLEXIN_DIR, "ZIPS")

# zip subfolders
TEMP_TRANSFERS_DIR = os.path.join(ZIP_DIR, "temp_transfers")
RECEIVED_FILES_DIR = os.path.join(ZIP_DIR, "received_files")
EXTRACTED_DIR = os.path.join(ZIP_DIR, "extracted")