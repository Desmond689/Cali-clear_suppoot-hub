from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

def rate_limit(limit):
    def decorator(fn):
        fn = limiter.limit(limit)(fn)
        return fn
    return decorator
