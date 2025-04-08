import asyncio
import typing


def create_future():
    return asyncio.get_running_loop().create_future()


def create_task(coro):
    return asyncio.get_running_loop().create_task(coro)
