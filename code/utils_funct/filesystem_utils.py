import datetime as dt
import os
from typing import Generator, TypedDict, List, Dict
from pathlib import Path

from client.paths import LOG_DIR, DATA_DIR, FLEXIN_DIR, CONFIG_DIR, ZIP_DIR



class FolderInfo(TypedDict):
    year        :   str
    month       :   str
    day         :   str
    hour        :   str
    minute      :   str
    folder_name :   str
    rel_path    :   str
    datetime    :   str



class ImageInfo(TypedDict):
    img_name            :   str # 202504241014-0.jpg
    parent_folder       :   str # 202504241014
    year                :   str # 2025
    month               :   str # 04
    day                 :   str # 24
    hour                :   str # 10
    minute              :   str # 14
    img_id              :   int # 0


class RootFolderMissing(Exception):
    pass

def fs_get_last_folder(root_folder : str) -> FolderInfo:
    '''
    Get the last created folder in the file system, this is the folder currently in production, this is still increasing so should be skipped
    Args:
        root_folder (str): path to the root folder that contains the images
    
    Returns (FolderInfo):
        the last created folder

    Raises:
        Folder not found when root_folder doesn't exists
    '''
    if not os.path.isdir(root_folder):
        raise RootFolderMissing(f"Folder not found: {root_folder}")


    # Get all the year folders in the root folder, check if are of type directory
    year_folders = [folder for folder in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, folder))]
    if len(year_folders) == 0:
        # Tree not populated yet (e.g. very first run): nothing to skip
        return None
    # Get the year folder most recent
    max_year = max(year_folders)
    year_path = os.path.join(root_folder, max_year)

    months_folders = [folder for folder in os.listdir(year_path) if os.path.isdir(os.path.join(year_path, folder))]
    if len(months_folders) == 0:
        return None
    max_month = max(months_folders)
    month_path = os.path.join(year_path, max_month)

    reel_folders = [folder for folder in os.listdir(month_path) if os.path.isdir(os.path.join(month_path, folder))]
    if len(reel_folders) == 0:
        return None
    last_reel = max(reel_folders)

    extracted_info = extract_folder_info(last_reel)

    return extracted_info



def walk_img_directories(root_folder : str) -> Generator[FolderInfo, None, None]:
    """
    Walk through the folders tree in root_folder in order and return the leaves folder containing the images

    Args:
            root_folder (str): path to the root folder that contains the images

    return:
        a dict with all the useful information on the folder
        None if no leaves folder is found

    Raises:
            Folder not found when root_folder doesn't exists
    """

    if not os.path.isdir(root_folder):
        print("Folder not found raising error")
        raise RootFolderMissing(f"Root folder not found: {root_folder}")

    #Get all the year folders in the root folder, check if are of type directory
    year_folders = [folder for folder in sorted(os.listdir(root_folder)) if os.path.isdir(os.path.join(root_folder, folder))]
    if len(year_folders) == 0:
        yield None
    for year in year_folders:
        year_path = os.path.join(root_folder, year)
        months_folders = [folder for folder in sorted(os.listdir(year_path)) if os.path.isdir(os.path.join(year_path, folder))]
        if len(months_folders) == 0:
                yield None
        for month in months_folders:
            month_path = os.path.join(year_path, month)
            imgs_folders = [folder for folder in sorted(os.listdir(month_path)) if os.path.isdir(os.path.join(month_path, folder))]
            if len(imgs_folders) == 0:
                            yield None
            for img_folder in imgs_folders:
                folder_info = extract_folder_info(img_folder)
                yield folder_info



def extract_img_info(img_name:str) -> ImageInfo:
        '''
        Given an img name in the form of -> "20240101120000-1.jpg"

        return (ImageInfo):
            a dictionary object formatted as an ImageInfo type
        '''

        no_extension = img_name.split(".")[0]
        parent_folder = no_extension.split("-")[0]
        id = no_extension.split("-")[1]
        year        =   parent_folder[0:4]
        month       =   parent_folder[4:6]
        day         =   parent_folder[6:8]
        hour        =   parent_folder[8:10]
        minute      =   parent_folder[10:12]

        return {
            'day'       : day,
            'hour'      : hour,
            'img_id'    : int(id),
            'img_name'  : img_name,
            'minute'    : minute,
            'month'     : month,
            'parent_folder' : parent_folder,
            'year'      : year
        }



def extract_folder_info(foldername: str) -> FolderInfo:
    '''
    Given a folder name in the form of -> "202401011200"

    return:
        a FolderInfo dictionary
    '''
    if len(foldername) != 12:
        return None

    year        =   foldername[0:4]
    month       =   foldername[4:6]
    day         =   foldername[6:8]
    hour        =   foldername[8:10]
    minute      =   foldername[10:12]

    rel_path    =   os.path.join(year, month, foldername)


    datetime    =   dt.datetime(int(year), int(month), int(day), int(hour), int(minute))

    return {
        "year"          :   year,
        "month"         :   month,
        "day"           :   day,
        "hour"          :   hour,
        "minute"        :   minute,
        "folder_name"   :   foldername,
        "rel_path"      :   rel_path,
        "datetime"      :   datetime,
    }