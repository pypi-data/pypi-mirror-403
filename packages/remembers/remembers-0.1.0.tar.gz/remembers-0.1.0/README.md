# 🥜 remembers

**Remember everything. Forget nothing (until you want to).**

A blazing-fast, async-friendly, thread-safe caching decorator for Python that just works. Drop it on any function and watch it remember results like magic.

## ✨ Features

- 🎯 **One decorator, zero config** - Just `@remember()` and you're done
- ⚡ **Async/await ready** - Works seamlessly with sync and async functions
- 🔒 **Thread-safe** - Battle-tested for concurrent access
- 💾 **Optional persistence** - Cache survives restarts with disk storage
- ⏱️ **TTL support** - Auto-expire entries when you want
- 🎨 **Smart key building** - Cache by specific args or nested paths
- 📊 **Built-in stats** - Track hits, misses, and hit rates

## Quick Start

```python
from remembers import remember

@remember(maxsize=128, ttl_seconds=300)
def expensive_api_call(user_id: int):
    # This only runs once per user_id (for 5 minutes)
    return fetch_user_data(user_id)

# Works with async too!
@remember(maxsize=64)
async def fetch_weather(city: str):
    return await weather_api.get(city)
```

## Advanced Usage

### Custom Cache Keys

```python
@remember(key_args=['user.id', 'config.api_key'])
def process_user(user, config):
    # Only caches based on user.id and config.api_key
    return expensive_processing(user, config)
```

### Persistent Cache

```python
@remember(maxsize=100, persist=True, cache_dir=".cache")
def expensive_computation(x: int):
    # Results survive restarts!
    return heavy_calculation(x)
```

### Check Cache Stats

```python
@remember(maxsize=50)
def my_function(arg):
    return process(arg)

my_function("test")
info = my_function.cache_info()
print(f"Hit rate: {info['hit_rate']:.2%}")
# Hit rate: 85.00%
```

## Installation

```bash
pip install remembers
```

## Requirements

- Python 3.12+

## License

MIT
