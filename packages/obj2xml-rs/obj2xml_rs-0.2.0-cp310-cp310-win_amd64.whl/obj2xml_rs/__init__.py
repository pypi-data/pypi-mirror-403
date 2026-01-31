from ._obj2xml_rs import unparse, parse

import asyncio
from functools import partial


async def unparse_async(*args, **kwargs):
    """
    Asynchronous wrapper for unparse.
    Runs the XML generation in a separate thread to avoid blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(unparse, *args, **kwargs))


async def parse_async(*args, **kwargs):
    """
    Asynchronous wrapper for parse.
    Runs the XML parsing in a separate thread to avoid blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(parse, *args, **kwargs))


__all__ = ["unparse", "unparse_async", "parse", "parse_async"]
