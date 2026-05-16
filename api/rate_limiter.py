import os
from slowapi import Limiter, _rate_limit_exceeded_handler as rate_limit_exceeded_handler
from slowapi.util import get_remote_address

RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")

limiter = Limiter(key_func=get_remote_address)
