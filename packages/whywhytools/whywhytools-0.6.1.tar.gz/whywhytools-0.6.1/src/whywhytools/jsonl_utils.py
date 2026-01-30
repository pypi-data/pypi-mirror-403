from pathlib import Path
from typing import Union
import os
import json
from .type_checker import check_file, check_obj_list

def read_jsonl(file: Union[str, Path]) -> list[dict]:
    """
    Read a JSONL file and return a list of dictionaries.

    Args:
        file (Union[str, Path]): The path to the JSONL file.

    Returns:
        list[dict]: A list containing the JSON objects read from the file.
    """
    check_file(file)
    
    df = []
    with open(file, mode='r', encoding='utf-8') as reader:
        line = reader.readline()
        while line:
            obj = json.loads(line)
            df.append(obj)
            line = reader.readline()
    return df

def write_jsonl(obj_list: Union[dict, list[dict]], file: Union[str, Path], force=False, silent=False) -> None:
    """
    Write a list of dictionaries to a JSONL file.

    Args:
        obj_list (Union[dict, list[dict]]): A single dictionary or a list of dictionaries to write.
        file (Union[str, Path]): The path to the output JSONL file.
        force (bool, optional): If True, overwrite the file if it exists. Defaults to False.
        silent (bool, optional): If True, suppress print messages. Defaults to False.
    """
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
    """
    Append a list of dictionaries to an existing JSONL file.

    Args:
        obj_list (Union[dict, list[dict]]): A single dictionary or a list of dictionaries to append.
        file (Union[str, Path]): The path to the JSONL file.
    """
    check_obj_list(obj_list)
    check_file(file)
    
    dir_path = os.path.dirname(file)
    if dir_path != '':
        os.makedirs(dir_path, exist_ok=True)
    
    with open(file, mode='a', encoding='utf-8', newline='\n') as fp:
        for obj in obj_list:
            json.dump(obj, fp, ensure_ascii=False)
            print(file=fp)