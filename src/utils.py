
import os

def delete_all_files(folder):
    for fn in os.listdir(folder):
        os.remove(os.path.join(folder,fn))