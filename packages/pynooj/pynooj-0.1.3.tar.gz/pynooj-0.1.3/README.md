# pynooj

Python library for parsing NooJ's dictionary files.

## Overview

**pynooj** is a Python library that parses NooJ dictionary files (`.dic`) and extracts lexical information including inflected forms, lemmas, grammatical categories, and morphological traits.

For more information about NooJ, visit the [NooJ website](https://nooj.univ-fcomte.fr/).

## Installation

```bash
pip install pynooj
```

## Usage

### Basic Example

```python
from pynooj import read_dic

# Parse a NooJ dictionary file
entries = read_dic("path/to/dictionary.dic")

# Each entry is a dictionary containing:
# - "inflected form": the word form
# - "lemma": the base form (optional)
# - "category": grammatical category (e.g., "V", "N", "A")
# - "traits": morphological attributes

for entry in entries:
    print(entry["inflected form"], "→", entry["lemma"])
    print(f"  Category: {entry['category']}")
    print(f"  Traits: {entry['traits']}")
```

### Dictionary File Format

NooJ dictionary files use a comma-separated format:

```
inflected_form,lemma,category+Trait1=Value1+Trait2=Value2
```

Examples:
```
amo,amare,V+Theme=INF+FLX=GP1_INF+GP=1
casa,casa,N+Number=SG+Gender=F
```

### API Reference

#### `read_dic(path)`

Parses a NooJ dictionary file and returns a list of lexical entries.

**Parameters:**
- `path` (str): Path to the `.dic` file

**Returns:**
- List of dictionaries, each containing:
  - `"inflected form"`: the word form (string)
  - `"lemma"`: the base form (string, optional)
  - `"category"`: grammatical category (string)
  - `"traits"`: dictionary of morphological traits (dict)


## Running Tests

To run the test suite with unittest:

```bash
python -m unittest discover -s tests
```

## Publishing to PyPI

### Prerequisites

Ensure you have the necessary tools installed:

```bash
pip install build twine
```

### Steps

1. **Update version** in `pyproject.toml`

2. **Build the package:**
   ```bash
   python -m build
   ```

3. **Upload to PyPI:**
   ```bash
   twine upload dist/*
   ```

4. **Upload to TestPyPI** (optional, for testing):
   ```bash
   twine upload --repository testpypi dist/*
   ```

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

See the [LICENSE](LICENSE) file for details.

## Related Resources

- [NooJ Official Website](https://nooj.univ-fcomte.fr/)
- [NooJ Manual](https://nooj.univ-fcomte.fr/)
- [GitHub Repository](https://github.com/crispyfunicular/pynooj)
