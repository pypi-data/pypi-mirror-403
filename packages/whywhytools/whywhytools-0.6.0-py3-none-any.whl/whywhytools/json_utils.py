from pathlib import Path
from typing import Union
import os
import json
from .type_checker import check_file

def read_json(file: Union[str, Path]):
    check_file(file)

    with open(file, mode='r', encoding='utf-8') as reader:
        df = json.load(reader)
    return df

def write_json(obj: Union[dict], file: Union[str, Path], force=False, silent=False):
    check_file(file)
    if not isinstance(obj, dict):
        raise TypeError("obj must be dict, got {}".format(type(obj).__name__))

    if os.path.exists(file) and force == False:
        print('[INFO] {} already exists.'.format(file))
        return
    
    dir_path = os.path.dirname(file)
    if dir_path != '':
        os.makedirs(dir_path, exist_ok=True)

    with open(file, mode='w', encoding='utf-8', newline='\n') as fp:
        json.dump(obj, fp, ensure_ascii=False, indent=4)
        print(file=fp)
    
    if not silent:
        print('[INFO] save to {}'.format(file))
