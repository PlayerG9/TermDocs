#!/usr/bin/python3
# -*- coding=utf-8 -*-
r"""

"""
import time
import inspect
import logging
import functools


def measured_function(fn):
    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            start = time.time()
            result = await fn(*args, **kwargs)
            end = time.time() - start
            logging.debug(f"Measured for {fn.__name__}: {round(end, 5)}s")
            return result
    else:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = fn(*args, **kwargs)
            end = time.time() - start
            logging.debug(f"Measured for {fn.__name__}: {round(end, 5)}s")
            return result

    return wrapper
