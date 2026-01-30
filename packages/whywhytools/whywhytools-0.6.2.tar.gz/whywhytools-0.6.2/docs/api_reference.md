# API Reference

Detailed documentation for `whywhytools` functions.

## JSON Lines (`.jsonl`)

Utilities for handling JSON Lines files.

### `read_jsonl`

```python
def read_jsonl(file: Union[str, Path]) -> list[dict]
```

Read a JSONL file and return a list of dictionaries.

**Args:**
* **file** (`Union[str, Path]`): The path to the JSONL file.

**Returns:**
* `list[dict]`: A list containing the JSON objects read from the file.

---

### `write_jsonl`

```python
def write_jsonl(obj_list: Union[dict, list[dict]], file: Union[str, Path], force=False, silent=False) -> None
```

Write a list of dictionaries to a JSONL file.

**Args:**
* **obj_list** (`Union[dict, list[dict]]`): A single dictionary or a list of dictionaries to write.
* **file** (`Union[str, Path]`): The path to the output JSONL file.
* **force** (`bool`, optional): If True, overwrite the file if it exists. Defaults to False.
* **silent** (`bool`, optional): If True, suppress print messages. Defaults to False.

---

### `append_jsonl`

```python
def append_jsonl(obj_list: Union[dict, list[dict]], file: Union[str, Path]) -> None
```

Append a list of dictionaries to an existing JSONL file.

**Args:**
* **obj_list** (`Union[dict, list[dict]]`): A single dictionary or a list of dictionaries to append.
* **file** (`Union[str, Path]`): The path to the JSONL file.

## JSON (`.json`)

Utilities for handling standard JSON files.

### `read_json`

```python
def read_json(file: Union[str, Path]) -> dict
```

Read a JSON file and return its content.

**Args:**
* **file** (`Union[str, Path]`): The path to the JSON file.

**Returns:**
* `dict`: The JSON object read from the file.

---

### `write_json`

```python
def write_json(obj: Union[dict], file: Union[str, Path], force=False, silent=False) -> None
```

Write a dictionary to a JSON file.

**Args:**
* **obj** (`Union[dict]`): The dictionary object to write.
* **file** (`Union[str, Path]`): The path to the output JSON file.
* **force** (`bool`, optional): If True, overwrite the file if it exists. Defaults to False.
* **silent** (`bool`, optional): If True, suppress print messages. Defaults to False.

**Raises:**
* `TypeError`: If obj is not a dictionary.

## Pickle (`.pkl`)

Utilities for handling Python pickle files.

### `load_pickle`

```python
def load_pickle(file: Union[str, Path]) -> Any
```

Load an object from a pickle file.

**Args:**
* **file** (`Union[str, Path]`): The path to the pickle file.

**Returns:**
* `Any`: The object loaded from the pickle file.

---

### `save_pickle`

```python
def save_pickle(obj, file: Union[str, Path], force=False, silent=False) -> None
```

Save an object to a pickle file.

**Args:**
* **obj** (`Any`): The object to save.
* **file** (`Union[str, Path]`): The path to the output pickle file.
* **force** (`bool`, optional): If True, overwrite the file if it exists. Defaults to False.
* **silent** (`bool`, optional): If True, suppress print messages. Defaults to False.
