# lazyval

A lazy evaluation wrapper for Python that defers function execution until the value is actually needed.

## Installation

```bash
pip install lazyval
```

With optional dependencies:

```bash
pip install lazyval[yaml]    # YAML serialization support
pip install lazyval[jinja]   # Jinja2 template support
```

## Quick Start

```python
from lazyval import Lazy

def expensive_query():
    print("Executing query...")
    return {"name": "Alice", "score": 95}

# Wrap the function - nothing executes yet
data = Lazy(expensive_query)

# Function executes only when value is accessed
print(data["name"])  # Prints "Executing query..." then "Alice"
print(data["score"]) # Just prints "95" (cached)
```

## Features

### Deferred Evaluation

The wrapped function only executes when you actually use the value:

```python
lazy_val = Lazy(lambda: 42)
# Nothing has executed yet

if lazy_val > 10:  # Function executes here
    print("Large value")
```

### Automatic Caching

Once evaluated, the result is cached:

```python
lazy_val = Lazy(expensive_function)
x = lazy_val + 1  # Executes function
y = lazy_val + 2  # Uses cached value
```

### Works with JSON

```python
import json
from lazyval import Lazy, dumps, LazyJSONEncoder

data = {"value": Lazy(lambda: 42)}

# Option 1: Use convenience function
json_str = dumps(data)

# Option 2: Use encoder class
json_str = json.dumps(data, cls=LazyJSONEncoder)
```

### Works with YAML

```python
import yaml
from lazyval import Lazy

data = {"value": Lazy(lambda: 42)}
yaml_str = yaml.dump(data)  # Outputs: value: 42
```

### Works with Jinja2 Templates

```python
from jinja2 import Template
from lazyval import Lazy

template = Template("Hello, {{ name }}!")
lazy_name = Lazy(lambda: "World")
result = template.render(name=lazy_name)  # "Hello, World!"
```

### Full Operator Support

```python
lazy_val = Lazy(lambda: 10)

# Arithmetic
lazy_val + 5   # 15
lazy_val * 2   # 20
10 - lazy_val  # 0

# Comparisons
lazy_val > 5   # True
lazy_val == 10 # True

# Container operations
lazy_list = Lazy(lambda: [1, 2, 3])
lazy_list[0]        # 1
len(lazy_list)      # 3
2 in lazy_list      # True
list(lazy_list)     # [1, 2, 3]

# Attribute access
lazy_str = Lazy(lambda: "hello")
lazy_str.upper()    # "HELLO"
```

### Decorator Syntax

```python
from lazyval import lazy

@lazy
def config():
    return load_config_from_file()

# Use like a regular value
if config["debug"]:
    print("Debug mode")
```

## API Reference

### `Lazy(func)`

Create a lazy wrapper around a callable.

- `func`: A zero-argument callable that returns the value

### Properties and Methods

- `lazy_val.is_evaluated` - Check if the value has been computed
- `lazy_val.force()` - Force evaluation and return the value

### JSON Functions

- `dumps(obj, **kwargs)` - JSON dumps with Lazy support
- `loads(s, **kwargs)` - JSON loads (convenience wrapper)
- `LazyJSONEncoder` - Custom JSON encoder class
- `lazy_json_default(obj)` - Default function for `json.dumps()`

## Requirements

- Python 3.10+

## License

MIT
