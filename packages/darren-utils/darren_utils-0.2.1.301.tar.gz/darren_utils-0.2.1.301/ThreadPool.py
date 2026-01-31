import threading
import queue
import time
from typing import Callable, Any, Optional, List


class DarrenThreadPool:
    """
    一个支持:
    - 设置线程数
    - 投递任务
    - 查询正在执行数 / 空闲线程数 / 是否空闲
    - 暂停 / 恢复
    - 销毁
    的简单线程池实现。
    """

    def __init__(self, num_threads: int):
        if num_threads <= 0:
            raise ValueError("线程数必须 > 0")

        self._num_threads = num_threads
        self._task_queue: "queue.Queue[tuple[Callable, tuple, dict, str]]" = queue.Queue()
        self._threads: List[threading.Thread] = []

        self._running_count = 0
        self._lock = threading.Lock()

        self._stop_event = threading.Event()
        self._pause_event = threading.Event()  # True=暂停

        self._task_seq = 0

        for i in range(num_threads):
            t = threading.Thread(target=self._worker, name=f"DarrenPool-Worker-{i+1}", daemon=True)
            self._threads.append(t)
            t.start()

    @classmethod
    def 创建(cls, 线程数: int) -> "DarrenThreadPool":
        return cls(线程数)

    def _worker(self):
        while not self._stop_event.is_set():
            while self._pause_event.is_set() and not self._stop_event.is_set():
                time.sleep(0.05)

            try:
                func, args, kwargs, _task_name = self._task_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            with self._lock:
                self._running_count += 1

            try:
                func(*args, **kwargs)
            except Exception:
                # 防止 worker 线程退出
                pass
            finally:
                with self._lock:
                    self._running_count -= 1
                self._task_queue.task_done()

    def 投递任务(self, func: Callable[..., Any], *args, 任务名: Optional[str] = None, **kwargs) -> str:
        if self._stop_event.is_set():
            raise RuntimeError("线程池已销毁，无法投递任务")

        with self._lock:
            self._task_seq += 1
            task_id = f"task-{self._task_seq}"

        if 任务名 is None:
            任务名 = task_id

        self._task_queue.put((func, args, kwargs, 任务名))
        return task_id

    def 取线程总数(self) -> int:
        return self._num_threads

    def 取正在执行数(self) -> int:
        with self._lock:
            return self._running_count

    def 取空闲线程数(self) -> int:
        with self._lock:
            return max(self._num_threads - self._running_count, 0)

    def 取是否空闲(self) -> bool:
        with self._lock:
            running = self._running_count
        return self._task_queue.empty() and running == 0

    def 暂停(self):
        self._pause_event.set()

    def 恢复(self):
        self._pause_event.clear()

    def 销毁(self, 等待任务完成: bool = True, 超时: Optional[float] = None):
        if 等待任务完成:
            try:
                self._task_queue.join()
            except Exception:
                pass

        self._stop_event.set()
        self._pause_event.clear()

        start = time.time()
        for t in self._threads:
            remaining: Optional[float]
            if 超时 is None:
                remaining = None
            else:
                elapsed = time.time() - start
                remaining = max(超时 - elapsed, 0)
                if remaining <= 0:
                    break
            try:
                t.join(timeout=remaining)
            except RuntimeError:
                pass

