# jp-prefectures-simple

Japanese prefecture names and JIS X 0401 codes converter.

This package has no external dependencies.

## Installation

```bash
pip install jp-prefectures-simple
```

## Usage

### Python API

You can import functions directly from the package:

```python
from jp_prefectures_simple import name2code, code2name

# Convert name to code
code = name2code("東京都")
print(code)  # "13"

# Convert code to name
name = code2name(13)
print(name)  # "東京都"

name = code2name("13")
print(name)  # "東京都"

# Convert list of names to codes
codes = name2code(["北海道", "東京都"])
print(codes)  # ["01", "13"]

# Convert list of codes to names
names = code2name([1, "13"])
print(names)  # ["北海道", "東京都"]
```
