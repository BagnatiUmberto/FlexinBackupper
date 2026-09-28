import os
import sys

from utils_funct import filesystem_utils

def main():
    total_imgs_count = 0
    imgs_present_count = 0

    with open("result.txt", 'w') as file:
        src_path = "C:\\Users\\bagnati.umberto\\Documents\\Projects\\Scambio Dati DB Flexin\\misc\\Img_copy"
        dest_path = "C:\\Users\\bagnati.umberto\\AppData\\Local\\FlexinBackupper\\server\\ZIPS\\extracted\\FlexinName"

        last_folder = filesystem_utils.fs_get_last_folder(src_path)

        years_folders = os.listdir(src_path)
        years_folders = sorted(years_folders)

        for year_folder in years_folders:
            if os.path.isdir(os.path.join(src_path, year_folder)):
                months_folders = os.listdir(os.path.join(src_path, year_folder))
                months_folders = sorted(months_folders)

                for month_folder in months_folders:
                    if os.path.isdir(os.path.join(src_path, year_folder, month_folder)):                
                        defects_folders = os.listdir(os.path.join(src_path, year_folder, month_folder))
                        defects_folders = sorted(defects_folders)

                        for defect_folder in defects_folders:
                            defects_imgs = os.listdir(os.path.join(src_path, year_folder, month_folder, defect_folder))
                            defects_imgs = sorted(defects_imgs)

                            file.write(f"FOLDER: {defect_folder}\n")
                            for defect_img in defects_imgs:
                                total_imgs_count += 1                        
                                present = os.path.exists(os.path.join(dest_path, year_folder, month_folder, defect_folder, defect_img))
                                plch = ""

                                if present:
                                    imgs_present_count +=1
                                    plch = "present"
                                else:
                                    plch = "NOT present"

                                file.write(f"img: {defect_img} - {plch}\n")

        file.write(f"Total num of imgs: {total_imgs_count}\n")
        file.write(f"Total num of present: {imgs_present_count}\n")
        file.write(f"Completness %: {imgs_present_count * 100 / total_imgs_count}\n")

if __name__ == "__main__":
    main()