from pathlib import Path
from typing import Union
import os
from .type_checker import check_file

import pickle
def load_pickle(file: Union[str, Path]):
    check_file(file)

    with open(file, 'rb') as f:
        obj = pickle.load(f)
    return obj

def save_pickle(obj, file: Union[str, Path], force=False, silent=False):
    check_file(file)

    if os.path.exists(file) and force == False:
        print('[INFO] {} already exists.'.format(file))
        return
    
    dir_path = os.path.dirname(file)
    if dir_path != '':
        os.makedirs(dir_path, exist_ok=True)
    
    with open(file, 'wb') as f:
        pickle.dump(obj, f)
    
    if not silent:
        print('[INFO] save to {}'.format(file))
