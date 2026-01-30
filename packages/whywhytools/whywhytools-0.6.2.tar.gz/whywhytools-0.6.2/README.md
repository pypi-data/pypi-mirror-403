# whywhytools

whywhytools is a lightweight Python package for reading and writing JSON, JSON Lines (`.jsonl`), and Pickle files. It provides simple and intuitive APIs for handling these common data formats.

## Installation

You can install this package using pip:

```bash
pip install whywhytools
```

## Quickstart

### JSON Lines (`.jsonl`)

Handle `.jsonl` files, supporting read, write, and append operations.

##### Write JSONL File

```python
from whywhytools import write_jsonl

data = [
    {'id': 'data-1', 'text': 'hello world'},
    {'id': 'data-2', 'text': 'whywhytools is awesome'}
]

# Write to file
write_jsonl(data, 'output.jsonl') # [INFO] save to output.jsonl

# If file exists
write_jsonl(data, 'output.jsonl') # [INFO] output.jsonl already exists.

# Force overwrite existing file
write_jsonl(data, 'output.jsonl', force=True) # [INFO] save to output.jsonl

# Silent mode (not print any message)
write_jsonl(data, 'output.jsonl', force=True, silent=True)
```

##### Append to JSONL File

```python
from whywhytools import append_jsonl

new_data = [{'id': 'data-3', 'text': 'new line'}]
append_jsonl(new_data, 'output.jsonl')
```

##### Read JSONL File

```python
from whywhytools import read_jsonl

data = read_jsonl('output.jsonl')
print(data)
# [{'id': 'data-1', 'text': 'hello world'}, {'id': 'data-2', 'text': 'whywhytools is awesome'}, {'id': 'data-3', 'text': 'new line'}]
```

### JSON (`.json`)

Handle standard `.json` files.

##### Write JSON File

```python
from whywhytools import write_json

data = {'project': 'whywhytools', 'version': '0.1.0'}

# Write to file
write_json(data, 'config.json')
```

##### Read JSON File

```python
from whywhytools import read_json

config = read_json('config.json')
print(config)
```

### Pickle (`.pkl`)

Handle Python's pickle serialization format.

##### Save Pickle File

```python
from whywhytools import save_pickle

model_data = {'weights': [0.1, 0.5, 0.9], 'bias': 0.01}
save_pickle(model_data, 'model.pkl')
```

##### Load Pickle File

```python
from whywhytools import load_pickle

data = load_pickle('model.pkl')
print(data)
```

## License

MIT

