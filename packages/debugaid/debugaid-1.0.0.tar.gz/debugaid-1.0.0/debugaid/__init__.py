__version__ = "1.0.0"
__author__ = "FelineFantasy"

import time
import sys
import os


def time_counter(code):
    """Measures execution time of Python code."""
    try:
        start = time.perf_counter()
        exec(code)
        end = time.perf_counter()
        return f"Execution time: {end - start:.15f} seconds"
    except Exception as error:
        return f"Error: {error}"


def size_var(var, unit):
    """Shows memory size of a variable."""
    try:
        size_in_bytes = sys.getsizeof(var)

        if unit == "bits":
            return f"{size_in_bytes * 8} bits"
        elif unit == "bytes":
            return f"{size_in_bytes} bytes"
        elif unit == "kb":
            return f"{size_in_bytes / 1024:.2f} KB"
        elif unit == "mb":
            return f"{size_in_bytes / (1024 ** 2):.2f} MB"
        elif unit == "gb":
            return f"{size_in_bytes / (1024 ** 3):.2f} GB"
        else:
            return "Unknown unit of measurement"
    except Exception as error:
        return f"Error: {error}"


def size_file(file_name, unit):
    """Shows memory size of a file."""
    try:
        size_in_bytes = os.path.getsize(file_name)

        if unit == "bits":
            return f"{size_in_bytes * 8} bits"
        elif unit == "bytes":
            return f"{size_in_bytes} bytes"
        elif unit == "kb":
            return f"{size_in_bytes / 1024:.2f} KB"
        elif unit == "mb":
            return f"{size_in_bytes / (1024 ** 2):.2f} MB"
        elif unit == "gb":
            return f"{size_in_bytes / (1024 ** 3):.2f} GB"
        else:
            return "Unknown unit of measurement"
    except Exception as error:
        return f"Error: {error}"