import asyncio
import logging
import threading
from concurrent.futures import Future
from typing import Optional, Coroutine, Any, TypeVar, Self

logger = logging.getLogger(__name__)


T = TypeVar("T")

class RegistryThreadLoop:
    __thread_loop: Optional[Self] = None
    """服务注册线程循环"""
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ready_event = threading.Event()  # 用于信令，确保线程已启动

    def _run_loop(self):
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            # 发送 "准备就绪" 信号
            self._ready_event.set()
            # 永久运行循环
            self._loop.run_forever()
        except Exception as e:
            logger.error(f"Registry worker thread failed: {e}")
            self._ready_event.set()  # 即使失败也要取消阻塞
        finally:
            if self._loop.is_running():
                self._loop.close()
            logger.info("Registry worker loop exited.")

    def start(self):
        """启动工作线程。"""
        if self._thread:
            logger.warning("Registry worker thread already started.")
            return

        logger.info("Starting Registry worker thread...")
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="RegistryWorker")
        self._thread.start()

        # 阻塞，直到 _run_loop 发出 "准备就绪" 信号
        self._ready_event.wait(timeout=10)

    async def run(self, coro: Coroutine[Any, Any, T]) -> T:
        """
        在工作线程中安全地运行一个协程，并异步等待其结果。

        Args:
            coro: 要在工作线程中执行的协程。

        Returns:
            协程的返回值 (类型为 T)。
        """
        if not self._thread or not self._loop:
            return await coro if coro else None
            # raise RuntimeError("Registry worker thread not started.")

        try:
            caller_loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError("run() must be called from within a running asyncio loop.")

        queue = asyncio.Queue(1)

        def _thread_safe_callback(future: asyncio.Future):
            caller_loop.call_soon_threadsafe(queue.put_nowait, future)

        future_ = asyncio.run_coroutine_threadsafe(coro, self._loop)
        future_.add_done_callback(_thread_safe_callback)

        f_result: Future = await queue.get()
        queue.task_done()

        # .result() 将返回类型 T 或引发异常
        return f_result.result()


    """服务注册线程循环"""
    @classmethod
    def get(cls, new_thread: bool = True) -> Self:
        if not cls.__thread_loop:
            thread_loop = RegistryThreadLoop()
            if new_thread:
                thread_loop.start()
            cls.__thread_loop = thread_loop
        return cls.__thread_loop

