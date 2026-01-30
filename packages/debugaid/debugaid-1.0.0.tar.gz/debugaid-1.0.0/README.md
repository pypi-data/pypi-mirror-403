# DebugAid

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)](https://pypi.org/project/debugaid/)

### DebugAid is a lightweight Python utility for performance analysis and memory profiling.

## Features

- **Precision Timing** - Measure code execution time with high accuracy
- **Memory Profiling** - Analyze memory usage of variables and files
- **Multiple Units** - Support for bits, bytes, KB, MB, GB
- **Simple API** - Intuitive and easy-to-use functions

## Installation

```bash
pip install debugaid
```

## Quick Start

```python
import debugaid

# Measure execution time
time_result = debugaid.time_counter("sum([i**2 for i in range(10000)])")
print(time_result)  # Execution time: 0.000627599998552 seconds

# getting the memory of a variable
my_list = [i for i in range(10000)]
size_result = debugaid.size_var(my_list, "kb")
print(size_result)  # 876.23 KB

# Analyze file size
file_size = debugaid.size_file("data.csv", "mb")
print(file_size)  # 2.45 MB
```

## License
MIT License