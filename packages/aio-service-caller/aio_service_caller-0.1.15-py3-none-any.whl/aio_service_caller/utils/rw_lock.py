import asyncio
from contextlib import asynccontextmanager


class RWLock:
    """
    写优先
    """
    def __init__(self):
        self._cond = asyncio.Condition()
        self._active_readers = 0
        self._active_writer = False
        self._waiting_writers = 0

    async def acquire_read(self):
        async with self._cond:
            while self._active_writer or self._waiting_writers > 0:
                await self._cond.wait()
            self._active_readers += 1

    async def release_read(self):
        async with self._cond:
            self._active_readers -= 1
            if self._active_readers == 0:
                self._cond.notify_all()

    async def acquire_write(self):
        async with self._cond:
            self._waiting_writers += 1
            try:
                while self._active_writer or self._active_readers > 0:
                    await self._cond.wait()
                self._active_writer = True
            finally:
                self._waiting_writers -= 1

    async def release_write(self):
        async with self._cond:
            self._active_writer = False
            self._cond.notify_all()

    @asynccontextmanager
    async def r_locked(self):
        await self.acquire_read()
        try:
            yield
        finally:
            await self.release_read()

    @asynccontextmanager
    async def w_locked(self):
        await self.acquire_write()
        try:
            yield
        finally:
            await self.release_write()