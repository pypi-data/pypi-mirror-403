# TagMap

A fast, efficient data structure for managing tags and metadata in Python, built with C++ and pybind11.

## Overview

TagMap is a specialized dictionary-like data structure optimized for managing multiple tags per key. It supports efficient queries for keys with specific tag combinations.

## Features

- Fast tag-based queries with intersection (all-of) and union (any-of) operations
- Efficient tag addition and removal
- Multiple query methods for flexible data retrieval
- Built on high-performance C++ implementation

## Installation

```bash
uv pip install tagmap
```

## Usage

```python
import tagmap

# Create a TagMap
m = tagmap.TagMap()

# Add entries with tags
m["alice"] = {"dev", "python"}
m["bob"] = {"dev", "cpp"}
m["carol"] = ["design", "python"]

# Query all entries with both "dev" and "python"
results = m.query("dev", "python")

# Query entries with either "python" OR "ops"
results = m.query_any("python", "ops")

# Check if an entry has a tag
has_tag = m.has_tag("alice", "python")

# Add/remove tags
m.add_tag("alice", "ml")
m.remove_tag("bob", "dev")
```

## Building from Source

```bash
# Install build dependencies
uv pip install pybind11

# Build and install in development mode
uv pip install -e .

# Or build directly
make
```
