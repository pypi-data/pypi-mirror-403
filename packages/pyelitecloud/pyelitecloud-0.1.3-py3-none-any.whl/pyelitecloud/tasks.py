

import asyncio
import threading


class AsyncTaskHelper:
    """
    Helper to unify async task create, sleep and stop
    """
    def __init__(self, target_function, *args, **kwargs):
        self.target_function = target_function
        self.args = args
        self.kwargs = kwargs

        self.result = None
        self._task = None
        self._stop_event = asyncio.Event()
        self._wakeup_event = asyncio.Event()

    async def start(self):
        coro = self.target_function(*self.args, **self.kwargs)
        self._task = asyncio.create_task(coro=coro, name=self.target_function.__name__)
        return self
    
    async def stop(self):
        try:
            self._stop_event.set()
            self._wakeup_event.set()
            
            self._result = await self._task # await the task to allow it to finish and cleanup
        except asyncio.CancelledError:
            pass

        return self.result
    
    def is_stop_requested(self):
        return self._stop_event.is_set()

    async def wakeup(self):
        self._wakeup_event.set()
    
    async def wait_for_wakeup(self, timeout: float):
        """Returns True if stop_event was set, False on timeout"""
        try:
            await asyncio.wait_for(self._wakeup_event.wait(), timeout=timeout)
            self._wakeup_event.clear()
            return True

        except asyncio.TimeoutError:
            return False

         
class TaskHelper(threading.Thread):
    """
    Helper to unify sync task create, sleep and stop
    """
    def __init__(self, target_function, *args, **kwargs):
        super().__init__()
        self.target_function = target_function
        self.args = args
        self.kwargs = kwargs

        self.name = target_function.__name__
        self.result = None
        self._task = None
        self._stop_event = threading.Event()
        self._wakeup_event = threading.Event()

    def start(self):
        super().start()
        return self

    def run(self):
        """Called internally after start()"""
        self.result = self.target_function(*self.args, **self.kwargs)

    def stop(self):
        self._stop_event.set()
        self._wakeup_event.set()
        
        super().join()
        return self.result
    
    def is_stop_requested(self):
        return self._stop_event.is_set()
    
    def wakeup(self):
        self._wakeup_event.set()
        
    def wait_for_wakeup(self, timeout: float) -> bool:
        """Returns True if stop_event was set, False on timeout"""
        res = self._wakeup_event.wait(timeout=timeout)
        self._wakeup_event.clear()
        return res
         
    