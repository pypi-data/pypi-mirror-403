
# humanbytes

`humanbytes` is a simple Python package to convert bytes into human-readable sizes using either decimal (KB, MB, ...) or binary (KiB, MiB, ...) units.

## Features
- Convert bytes to a human-readable string
- Supports both decimal (powers of 1000) and binary (powers of 1024) units
- Minimal, dependency-free, and easy to use


## Installation

```bash
pip install humanbytes
```

## Usage


```python

from humanbytes import humanbytes

print(humanbytes(1536))                # 1.54 KB
print(humanbytes(1536, binary=True))   # 1.50 KiB
print(humanbytes(10**9))               # 1.00 GB
print(humanbytes(2**30, binary=True))  # 1.00 GiB
```

### Parameters
- `num`: The number to convert (e.g., bytes)
- `binary`: If True, use binary units (KiB, MiB, ...). If False (default), use decimal units (KB, MB, ...)

## License

MIT License. See [LICENSE](LICENSE) for details.