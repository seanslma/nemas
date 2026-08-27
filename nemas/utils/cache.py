import json
import inspect
import functools
import threading
from cachetools import TTLCache
from collections.abc import Callable

CACHE_TIME_LIMIT = 60 * 60  # one hour
_ttl_cache = TTLCache(maxsize=128, ttl=CACHE_TIME_LIMIT)


def key_builder(f, namespace, exclude, *args, **kwargs):
    params = {}
    params['args'] = args
    if isinstance(exclude, str):
        exclude = [exclude]
    for k, v in kwargs.items():
        if exclude is not None and k in exclude:
            continue
        params[k] = v
    return f'{f.__name__}:{namespace}{json.dumps(params)}'


def ttl_cached(
    namespace: str = '',
    exclude: list[str] = None,
    key_builder: Callable = key_builder,
):
    def decorator(f):
        sig = inspect.signature(f)
        lock = threading.Lock()  # one lock per decorated function

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            use_cache = bound.arguments.get('cache', True)
            if not use_cache:
                return f(*args, **kwargs)

            key = key_builder(f, namespace, exclude, *args, **kwargs)
            with lock:
                if key in _ttl_cache:
                    return _ttl_cache[key]

            result = f(*args, **kwargs)
            with lock:
                _ttl_cache[key] = result
            return result

        return wrapper

    return decorator
