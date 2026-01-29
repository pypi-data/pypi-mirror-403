import sys
import time
import typing
import asyncio
import functools
import threading


# ==-----------------------------------------------------------------------------== #
# Universal functions decorators                                                    #
# ==-----------------------------------------------------------------------------== #
def timeout_repeat(function_or_coroutine: typing.Callable | None = None, *, timeout: int | float, repeat_delay: int | float = 0.0, repeat_on_values: typing.Iterable[typing.Any] = [None]):
    """Decorator, repeats function execution until timeout or expected value reached."""

    # If timeout is invalid value
    if timeout < 0:
        raise Exception("timeout argument have to be greater than `0`")

    # If repeat delay is invalid value
    if repeat_delay < 0:
        raise Exception("repeat delay have to be greater than `0`")

    # Decorator outer wrapper
    def decorator(function: typing.Callable):

        # Wrapper for sync version of function
        @functools.wraps(function)
        def sync_wrapper(*args: typing.Any, **kwargs: typing.Any) -> tuple[typing.Any, bool]:

            start_time = time.time()
            while (result := function(*args, **kwargs)) in repeat_on_values:

                # If timeout exceeded
                if time.time() - start_time > timeout:
                    return None, False

                # Delay until next repeat
                time.sleep(repeat_delay)

            else:
                return result, True

        @functools.wraps(function)
        async def async_wrapper(*args: typing.Any, **kwargs: typing.Any) -> tuple[typing.Any, bool]:

            start_time = time.time()
            while (result := (await function(*args, **kwargs))) in repeat_on_values:

                # If timeout exceeded
                if time.time() - start_time > timeout:
                    return None, False

                # Delay until next repeat
                await asyncio.sleep(repeat_delay)

            else:
                return result, True

        # Returning async decorator wrapper if function is coroutine else sync decorator wrapper
        return async_wrapper if asyncio.iscoroutinefunction(function) else sync_wrapper

    # If function decorated with arguments
    if function_or_coroutine is None:
        return decorator

    # If function decorated without arguments
    return decorator(function_or_coroutine)


def retry(function_or_coroutine: typing.Callable | None = None, *, retries: int = 1, retry_delay: int | float = 0.0):
    """Decorator, allows to retry function call if exception raises for several times."""

    # If retry times is invalid value
    if retries <= 0:
        raise Exception("retries argument have to be greater than `0`")

    # If retry interval is invalid value
    if retry_delay < 0:
        raise Exception("delay argument have to be greater or equals `0`")

    # Decorator outer wrapper
    def decorator(function: typing.Callable):

        # Wrapper for async version of function
        @functools.wraps(function)
        async def async_wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:

            # Last exception raised on coroutine call
            last_exception = None

            # Trying to call and return result on coroutine while succeed exceeded `retries` + 1 times
            for index in range(retries + 1):

                try:
                    return await function(*args, **kwargs)

                except BaseException as error:

                    # Saving last exception raised on coroutine call
                    last_exception = error

                # If there a more extra retry call coroutine
                if index != retries:
                    await asyncio.sleep(retry_delay)

            # Raising last saved exception
            raise last_exception

        # Wrapper for sync version of function
        @functools.wraps(function)
        def sync_wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:

            # Last exception raised on coroutine call
            last_exception = None

            # Trying to call and return result on function while succeed exceeded `times` + 1 times
            for index in range(retries + 1):

                try:
                    return function(*args, **kwargs)

                except BaseException as error:

                    # Saving last exception raised on coroutine call
                    last_exception = error

                # If there a more extra retry call coroutine
                if index != retries:
                    time.sleep(retry_delay)

            # Raising last saved exception
            raise last_exception

        # Returning async decorator wrapper if function is coroutine else sync decorator wrapper
        return async_wrapper if asyncio.iscoroutinefunction(function) else sync_wrapper

    # If function decorated with arguments
    if function_or_coroutine is None:
        return decorator

    # If function decorated without arguments
    return decorator(function_or_coroutine)


def raiseless(function_or_coroutine: typing.Callable | None = None):
    """Decorator, allows to catch raised function exception as return result instead of using of try-except block."""

    # Decorator outer wrapper
    def decorator(function: typing.Callable):

        # Wrapper for async version of function
        @functools.wraps(function)
        async def async_wrapper(*args: typing.Any, **kwargs: typing.Any) -> tuple[typing.Any, BaseException]:

            # Trying to call and return result of coroutine function
            try:
                return (await function(*args, **kwargs)), None

            except BaseException as error:
                return None, error

        # Wrapper for sync version of function
        @functools.wraps(function)
        def sync_wrapper(*args: typing.Any, **kwargs: typing.Any) -> tuple[typing.Any, BaseException]:

            # Trying to call and return result of function
            try:
                return function(*args, **kwargs), None

            except BaseException as error:
                return None, error

        # Returning async decorator wrapper if function is coroutine else sync decorator wrapper
        return async_wrapper if asyncio.iscoroutinefunction(function) else sync_wrapper

    # If function decorated with arguments
    if function_or_coroutine is None:
        return decorator

    # If function decorated without arguments
    return decorator(function_or_coroutine)


# ==-----------------------------------------------------------------------------== #
# Async functions decorators                                                        #
# ==-----------------------------------------------------------------------------== #
def task(coroutine: typing.Callable | None = None, *, name: str | None = None):
    """Decorator, wraps coroutine to make its able to run as background non-blocking task."""

    # Decorator outer wrapper
    def decorator(function: typing.Callable):

        # If coroutine is not awaitable function
        if not asyncio.iscoroutinefunction(function):
            raise Exception("`%s` decorator can only be applied to coroutine function" % sys._getframe().f_back.f_code.co_name)

        @functools.wraps(function)
        def wrapper(*args: typing.Any, **kwargs: typing.Any) -> asyncio.Task:

            # Wraps coroutine as a task and return its object
            return asyncio.create_task(function(*args, **kwargs), name=name)

        # Returning innter wrapper
        return wrapper

    # If function decorated with arguments
    if coroutine is None:
        return decorator

    # If function decorated without arguments
    return decorator(coroutine)


# ==-----------------------------------------------------------------------------== #
# Sync functions decorators                                                         #
# ==-----------------------------------------------------------------------------== #
def threaded(function: typing.Callable | None = None, *, name: str | None = None, daemon: bool | None = None, immediate_start: bool = False):
    """Decorator, wraps function to make its executes in its own system thread."""

    # Decorator outer wrapper
    def decorator(function: typing.Callable):

        # If function is awaitable function
        if asyncio.iscoroutinefunction(function):
            raise Exception("`%s` decorator can only be applied to sync function" % sys._getframe().f_back.f_code.co_name)

        @functools.wraps(function)
        def wrapper(*args: typing.Any, **kwargs: typing.Any) -> threading.Thread:

            # Wraps function as a thread
            thread = threading.Thread(target=function, args=args, kwargs=kwargs, name=name, daemon=daemon)

            # Returns thread handle or just start thread immediate on its call
            return thread if immediate_start else thread.start()

        # Returning innter wrapper
        return wrapper

    # If function decorated with arguments
    if function is None:
        return decorator

    # If function decorated without arguments
    return decorator(function)
