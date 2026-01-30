# velmu.ext.tasks
import asyncio
import inspect
import logging
import sys
import traceback
from typing import Any, Callable, Coroutine, Optional, Union, TypeVar

_log = logging.getLogger(__name__)

LF = TypeVar('LF', bound=Callable[..., Coroutine[Any, Any, Any]])

class Loop:
    """
    A background task loop.
    """
    def __init__(
        self, 
        coro: LF, 
        seconds: float = 0, 
        minutes: float = 0, 
        hours: float = 0, 
        count: Optional[int] = None, 
        reconnect: bool = True, 
        loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        self.coro = coro
        self.seconds = seconds
        self.minutes = minutes
        self.hours = hours
        self.count = count
        self.reconnect = reconnect
        self._loop = loop or asyncio.get_event_loop()
        
        self._task: Optional[asyncio.Task] = None
        self._injected_loop = None
        self._valid_exception = (OSError, asyncio.TimeoutError) # Exceptions to ignore handling if reconnect=True?
        
        self._before_loop = None
        self._after_loop = None
        self._error = None

        self._stop_next_iteration = False
        self._current_loop = 0
        self._next_iteration = None
        
        if self.seconds == 0 and self.minutes == 0 and self.hours == 0:
            raise ValueError("You must supply a time interval")

    async def _loop_logic(self, *args, **kwargs):
        try:
            if self._before_loop:
                await self._before_loop(*args, **kwargs)

            self._next_iteration = self._loop.time()
            # Loop
            while True:
                if self._stop_next_iteration:
                    return

                # Calculate Sleep
                now = self._loop.time()
                if self._next_iteration is None: 
                    self._next_iteration = now
                    
                if self._next_iteration > now:
                    await asyncio.sleep(self._next_iteration - now)
                
                # Execute
                try:
                    await self.coro(*args, **kwargs)
                    self._current_loop += 1
                    
                    if self.count is not None and self._current_loop >= self.count:
                        break
                except Exception as exc:
                    # Handle Error
                    if self._error:
                        await self._error(exc)
                    else:
                        print(f"Unhandled exception in task {self.coro.__name__}:", file=sys.stderr)
                        traceback.print_exc()
                        
                    if not self.reconnect:
                        raise exc

                # Schedule Next
                interval = self.seconds + (self.minutes * 60.0) + (self.hours * 3600.0)
                self._next_iteration = now + interval
                
        except asyncio.CancelledError:
            self._stop_next_iteration = False
            raise
        except Exception as e:
            # Fatal error
            print(f"Internal loop error: {e}")
        finally:
             if self._after_loop:
                await self._after_loop(*args, **kwargs)
             self._task = None

    def start(self, *args, **kwargs):
        """Starts the loop."""
        if self._task and not self._task.done():
            raise RuntimeError("Task is already running")
        
        self._task = self._loop.create_task(self._loop_logic(*args, **kwargs))
        return self._task

    def stop(self):
        """Stops the loop gracefully after current iteration."""
        if self._task and not self._task.done():
            self._stop_next_iteration = True

    def cancel(self):
        """Cancels the loop immediately."""
        if self._task and not self._task.done():
            self._task.cancel()

    def is_running(self) -> bool:
        """Checks if the loop is currently running."""
        return self._task is not None and not self._task.done()

    def restart(self, *args, **kwargs):
        """Restarts the loop."""
        self.cancel()
        self.start(*args, **kwargs)
        
    def before_loop(self, coro: LF) -> LF:
        self._before_loop = coro
        return coro

    def after_loop(self, coro: LF) -> LF:
        self._after_loop = coro
        return coro
        
    def error(self, coro: Callable[[Exception], Coroutine[Any, Any, Any]]):
        self._error = coro
        return coro


def loop(
    seconds: float = 0, 
    minutes: float = 0, 
    hours: float = 0, 
    count: Optional[int] = None, 
    reconnect: bool = True, 
    loop: Optional[asyncio.AbstractEventLoop] = None
):
    """
    Decorator to create a background task loop.
    """
    def decorator(func: LF) -> Loop:
        return Loop(func, seconds=seconds, minutes=minutes, hours=hours, count=count, reconnect=reconnect, loop=loop)
    return decorator
