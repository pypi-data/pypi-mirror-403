# dcache

A disk-based caching utility for Python functions.

## Installation

```bash
pip install cache_on_disk
```

## Usage

### Basic Usage

```python
from cache_on_disk import dcache

# For synchronous functions
@dcache
def expensive_function(x, y):
    # Some expensive computation
    return x + y

# For asynchronous functions
@dcache
async def async_expensive_function(x, y):
    # Some expensive async computation
    return x + y
```

### With Required Arguments

You can specify which keyword arguments are required for caching:

```python
@dcache(required_kwargs=["user_id"])
def get_user_data(user_id, include_history=False):
    # This will only be cached if user_id is provided as a keyword argument
    return {"user_id": user_id, "history": get_history(user_id) if include_history else None}
```

### Custom Cache Configuration

```python
from dcache import DCache

# Create a custom cache instance
my_cache = DCache(n_semaphore=50, cache_dir="/path/to/cache")

@my_cache
def my_function():
    # This will use the custom cache configuration
    pass
```

## License

MIT