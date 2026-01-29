from pathlib import Path
from typing import Union
import os
import json
from .type_checker import check_file, check_obj_list

def read_jsonl(file: Union[str, Path]):
    check_file(file)
    
    df = []
    with open(file, mode='r', encoding='utf-8') as reader:
        line = reader.readline()
        while line:
            obj = json.loads(line)
            df.append(obj)
            line = reader.readline()
    return df

def write_jsonl(obj_list: Union[dict, list[dict]], file: Union[str, Path], force=False, silent=False):
    check_obj_list(obj_list)
    check_file(file)
    
    if os.path.exists(file) and force == False:
        print('[INFO] {} already exists.'.format(file))
        return
    
    dir_path = os.path.dirname(file)
    if dir_path != '':
        os.makedirs(dir_path, exist_ok=True)
    
    with open(file, mode='w', encoding='utf-8', newline='\n') as fp:
        for obj in obj_list:
            json.dump(obj, fp, ensure_ascii=False)
            print(file=fp)
    
    if not silent:
        print('[INFO] save to {}'.format(file))


def append_jsonl(obj_list: Union[dict, list[dict]], file: Union[str, Path]) -> None:
    check_obj_list(obj_list)
    check_file(file)
    
    dir_path = os.path.dirname(file)
    if dir_path != '':
        os.makedirs(dir_path, exist_ok=True)
    
    with open(file, mode='a', encoding='utf-8', newline='\n') as fp:
        for obj in obj_list:
            json.dump(obj, fp, ensure_ascii=False)
            print(file=fp)