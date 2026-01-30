from pathlib import Path
from typing import Union

def check_obj_list(obj_list: Union[dict, list[dict]]):
    if isinstance(obj_list, dict):
        obj_list = [obj_list]
    elif not isinstance(obj_list, list):
        raise TypeError(f"obj_list must be a dict or list[dict]; got {type(obj_list).__name__}")
    
    for i, obj in enumerate(obj_list):
        if not isinstance(obj, dict):
            raise TypeError(f"obj_list must be list[dict]; got {type(obj).__name__} at index {i}")

def check_file(file: Union[str, Path]):
    if not isinstance(file, str):
        raise TypeError("file must be str, got {}".format(type(file).__name__))
