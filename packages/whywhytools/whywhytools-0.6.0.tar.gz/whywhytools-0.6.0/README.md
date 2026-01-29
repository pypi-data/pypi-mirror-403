# whywhytools
A lightweight Python package for reading and writing JSON Lines (`.jsonl`) files, providing simple APIs for line-based JSON data processing.



# Installation

```bash
pip install whywhytools
```



## Quickstart

##### write file

```python
from whywhytools import write_jsonl

ds = [{'text': 'hello world'}]
write_jsonl(ds, 'output.jsonl')
```

##### read file

```python
from whywhytools import read_jsonl

ds = read_jsonl('output.jsonl')
```

