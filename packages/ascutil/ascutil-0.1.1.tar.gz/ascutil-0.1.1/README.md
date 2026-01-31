# ascutil
Python bindings for fast .asc circuit mutation.

## Installation
```
pip install ascutil
```

## Usage
```
from ascutil import mutate

rows = list(range(16))
columns = list(range(54))
mutate("circuit_copy.asc", rows, columns, 0.5)
```

## Building
```
python3 -m venv .venv
source .venv/bin/activate
pip install maturin
maturin build --release
```