import warnings
import functools

# Python 3.13+ has @warnings.deprecated
if hasattr(warnings, "deprecated"):
    deprecated = warnings.deprecated
else:
    # fallback for Python 3.12-
    def deprecated(reason: str):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                warnings.warn(
                    f"{func.__name__} is deprecated: {reason}",
                    DeprecationWarning,
                    stacklevel=2,
                )
                return func(*args, **kwargs)
            return wrapper
        return decorator
