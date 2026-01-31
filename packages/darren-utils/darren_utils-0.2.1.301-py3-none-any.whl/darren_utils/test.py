import threading
import queue
import time
import logging
from typing import Callable, Any, Optional, List, Dict, Tuple, Union, Literal
from dataclasses import dataclass, field
from contextlib import contextmanager

# 全局日志配置（支持外部重写）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# 类型定义
TaskStatus = Literal["pending", "running", "success", "failed", "cancelled", "retrying"]
Priority = int  # 数字越大优先级越高，默认0
TaskCallback = Callable[["TaskInfo"], None]
WorkerStatus = Literal["idle", "running"]


@dataclass
class TaskInfo:
    """
    任务信息封装（彻底修复优先级队列比较问题）
    放弃dataclass自动排序，改用元组(优先级, 时间戳, 任务ID, 任务)封装到优先级队列
    """
    task_id: str
    task_name: str
    func: Callable[..., Any]
    priority: Priority = 0
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    callback: Optional[TaskCallback] = field(default=None)
    status: TaskStatus = field(default="pending")
    result: Any = field(default=None)
    exception: Optional[Exception] = field(default=None)
    create_time: float = field(default_factory=time.time)
    start_time: Optional[float] = field(default=None)
    end_time: Optional[float] = field(default=None)
    # （简化版）不再内置重试/超时，由调用方自行处理


@dataclass
class WorkerInfo:
    """工作线程信息封装，用于动态管理"""
    thread: threading.Thread
    status: WorkerStatus = "idle"
    last_work_time: float = field(default_factory=time.time)


class DarrenThreadPool:
    """
    最终稳定版线程池（修复优先级队列阻塞问题）
    """

    def __init__(
            self,
            num_threads: int,
            max_threads: Optional[int] = None,
            min_idle_threads: int = 1,
            idle_recycle_seconds: float = 30.0,
            default_priority: Priority = 0,
            task_done_callback: Optional[TaskCallback] = None
    ):
        """
        初始化线程池
        :param num_threads: 初始工作线程数
        :param max_threads: 最大线程数（动态扩容上限，None=等于初始线程数）
        :param min_idle_threads: 最小空闲线程数（回收时保留）
        :param idle_recycle_seconds: 空闲线程回收超时(秒)
        :param default_priority: 任务默认优先级
        :param task_done_callback: 全局任务完成回调
        """
        # 校验基础参数
        if num_threads <= 0:
            raise ValueError("初始线程数必须 > 0")
        self._max_threads = max_threads or num_threads
        self._min_idle_threads = max(min_idle_threads, 1)
        if num_threads > self._max_threads:
            raise ValueError(f"初始线程数({num_threads})不能超过最大线程数({self._max_threads})")

        # 核心配置（归一化管理）
        self._config = {
            "idle_recycle_seconds": idle_recycle_seconds,
            "default_priority": default_priority,
        }

        # 任务相关：优先级队列改用「元组(优先级, 时间戳, 任务ID, 任务)」封装
        # 时间戳用于优先级相同的任务按投递顺序执行，任务ID避免元组比较冲突
        self._task_queue = queue.PriorityQueue()
        self._task_map: Dict[str, TaskInfo] = {}  # task_id -> TaskInfo
        self._task_seq = 0  # 任务序列号
        self._global_task_callback = task_done_callback  # 全局任务回调

        # 线程相关（动态管理，替换原列表）
        self._workers: Dict[str, WorkerInfo] = {}  # worker_name -> WorkerInfo
        self._recycle_thread = threading.Thread(target=self._idle_worker_recycle, daemon=True, name="WorkerRecycle")

        # 线程安全锁
        self._task_lock = threading.Lock()  # 任务相关锁
        self._worker_lock = threading.RLock()  # 线程相关锁（改为可重入锁，避免同锁重入死锁）
        self._config_lock = threading.Lock()  # 配置相关锁

        # 控制事件
        self._stop_event = threading.Event()  # 销毁标记
        self._pause_event = threading.Event()  # 暂停标记（True=暂停）

        # 初始化启动
        self._start_workers(num_threads)  # 启动初始线程
        self._recycle_thread.start()  # 启动空闲线程回收线程
        logger.info(
            f"线程池初始化完成 | 初始线程：{num_threads} | 最大线程：{self._max_threads} | 最小空闲：{self._min_idle_threads}")

    def _start_worker(self) -> str:
        """启动单个工作线程，返回线程名"""
        with self._worker_lock:
            if len(self._workers) >= self._max_threads:
                raise RuntimeError(f"线程数已达上限({self._max_threads})，无法新增")
            worker_name = f"DarrenPool-Worker-{len(self._workers) + 1}"
            t = threading.Thread(target=self._worker, name=worker_name, daemon=True)
            self._workers[worker_name] = WorkerInfo(thread=t, status="idle")
            t.start()
        logger.info(f"工作线程启动：{worker_name} | 当前线程数：{len(self._workers)}")
        return worker_name

    def _start_workers(self, num: int):
        """批量启动工作线程"""
        for _ in range(num):
            self._start_worker()

    def _remove_worker(self, worker_name: str, force: bool = False) -> bool:
        """
        移除单个工作线程
        :param worker_name: 线程名
        :param force: 是否强制移除（即使线程正在运行）
        :return: 移除成功返回True
        """
        with self._worker_lock:
            worker = self._workers.get(worker_name)
            if not worker:
                logger.warning(f"移除线程失败：{worker_name} 不存在")
                return False
            if worker.status == "running" and not force:
                logger.warning(f"移除线程失败：{worker_name} 正在运行（非强制模式）")
                return False
            # 标记线程退出并移除
            del self._workers[worker_name]
        logger.info(f"工作线程已标记移除：{worker_name} | 当前线程数：{len(self._workers)}")
        return True

    def _idle_worker_recycle(self):
        """空闲线程自动回收（后台守护线程）"""
        while not self._stop_event.is_set():
            time.sleep(5)  # 每5秒检查一次
            if self._stop_event.is_set():
                break
            with self._worker_lock:
                # 计算空闲线程数
                idle_workers = {k: v for k, v in self._workers.items() if v.status == "idle"}
                if len(idle_workers) <= self._min_idle_threads:
                    continue
                # 回收超时的空闲线程
                now = time.time()
                recycle_candidates = [
                    name for name, info in idle_workers.items()
                    if now - info.last_work_time > self._config["idle_recycle_seconds"]
                ]
                # 保证回收后剩余空闲线程数 >= 最小空闲数
                need_recycle = len(recycle_candidates) - (len(idle_workers) - self._min_idle_threads)
                for name in recycle_candidates[:need_recycle]:
                    self._remove_worker(name)

    def _worker(self):
        """工作线程核心逻辑（无重试/超时，失败立即结束）"""
        worker_name = threading.current_thread().name
        logger.info(f"工作线程启动完成：{worker_name}")
        while not self._stop_event.is_set():
            # 处理暂停逻辑：暂停时阻塞，直到恢复或销毁
            if self._pause_event.is_set():
                time.sleep(0.05)
                continue

            # 更新线程状态为空闲
            with self._worker_lock:
                if worker_name in self._workers:
                    self._workers[worker_name].status = "idle"
                    self._workers[worker_name].last_work_time = time.time()

            # 从优先级队列取任务（修复：取元组后解析出任务）
            try:
                # 优先级队列存储的是 (-priority, timestamp, task_id, task)
                # 用负号实现“数字越大优先级越高”，timestamp保证同优先级按投递顺序执行
                priority_tuple = self._task_queue.get(timeout=0.1)
                task: TaskInfo = priority_tuple[3]  # 解析出真正的任务对象
            except queue.Empty:
                continue

            # 检查任务是否被取消（消费时判断，高效取消）
            with self._task_lock:
                if task.task_id not in self._task_map or self._task_map[task.task_id].status == "cancelled":
                    self._task_queue.task_done()
                    logger.info(f"任务已取消，跳过执行：{task.task_id}（{task.task_name}）")
                    continue
                # 更新任务状态为运行中
                task.status = "running"
                task.start_time = time.time()
                self._task_map[task.task_id] = task
            # 更新线程状态为运行中
            with self._worker_lock:
                if worker_name in self._workers:
                    self._workers[worker_name].status = "running"

            # 执行任务（简化：无重试/超时）
            task_result = None
            task_exception = None
            try:
                logger.info(
                    f"开始执行任务 | ID：{task.task_id} | 名称：{task.task_name} | 优先级：{task.priority}")
                task_result = task.func(*task.args, **task.kwargs)
            except Exception as e:
                task_exception = e
                logger.error(f"任务执行异常 | ID：{task.task_id} | 异常：{str(e)}", exc_info=True)
            finally:
                self._task_queue.task_done()
                with self._task_lock:
                    if task.task_id not in self._task_map:
                        return
                    current_task = self._task_map[task.task_id]
                    if task_exception:
                        current_task.status = "failed"
                        current_task.exception = task_exception
                    else:
                        current_task.status = "success"
                        current_task.result = task_result
                    current_task.end_time = time.time()
                    self._task_map[task.task_id] = current_task
                    # 执行回调
                    self._execute_task_callback(current_task)
                # 打印任务执行结果
                if current_task.start_time is not None and current_task.end_time is not None:
                    cost = round(current_task.end_time - current_task.start_time, 3)
                else:
                    cost = -1.0
                logger.info(
                    f"任务执行完成 | ID：{task.task_id} | 名称：{task.task_name} | 状态：{current_task.status} "
                    f"| 耗时：{cost}秒 | 结果：{current_task.result if current_task.status == 'success' else current_task.exception}"
                )
        # 线程退出逻辑
        logger.info(f"工作线程退出：{worker_name}")

    def _execute_task_callback(self, task: TaskInfo):
        """执行任务回调（全局+局部，局部优先）"""
        try:
            # 先执行任务局部回调
            if task.callback:
                task.callback(task)
            # 再执行全局回调
            elif self._global_task_callback:
                self._global_task_callback(task)
        except Exception as e:
            logger.error(f"任务回调执行失败 | ID：{task.task_id} | 异常：{str(e)}", exc_info=True)

    def _generate_task_id(self) -> str:
        """生成唯一任务ID（加锁保证线程安全）"""
        with self._task_lock:
            self._task_seq += 1
            return f"task-{int(time.time() * 1000)}-{self._task_seq}"

    # ------------------------------ 核心功能：任务操作 ------------------------------
    def submit_task(
            self,
            func: Callable[..., Any],
            *args,
            task_name: Optional[str] = None,
            priority: Optional[Priority] = None,
            callback: Optional[TaskCallback] = None, **kwargs
    ) -> str:
        """
        投递单个任务（修复：封装优先级元组入队）
        :param func: 任务函数
        :param args: 函数位置参数
        :param task_name: 任务名（可选）
        :param priority: 任务优先级（数字越大越高，默认取全局配置）
        :param callback: 任务局部回调（优先级高于全局回调）
        :param kwargs: 函数关键字参数
        :return: 任务ID
        """
        if self._stop_event.is_set():
            raise RuntimeError("线程池已销毁，无法投递任务")

        # 加载配置（局部参数优先，无则取全局）
        with self._config_lock:
            _priority = priority or self._config["default_priority"]
        # 生成任务ID和名称
        task_id = self._generate_task_id()
        task_name = task_name or task_id
        # 实例化TaskInfo（优先级直接存入字段）
        task = TaskInfo(
            task_id=task_id,
            task_name=task_name,
            func=func,
            priority=_priority,
            args=args,
            kwargs=kwargs,
            callback=callback,
        )

        # 记录任务并加入优先级队列（核心修复：封装成元组）
        with self._task_lock:
            self._task_map[task_id] = task
        # 元组格式：(-优先级, 时间戳, 任务ID, 任务对象)
        # 负号：实现“数字越大优先级越高”（PriorityQueue默认升序）
        # 时间戳：同优先级任务按投递顺序执行
        # 任务ID：避免同优先级+同时间戳时，元组比较到任务对象引发错误
        self._task_queue.put((-_priority, time.time(), task_id, task))

        # 动态扩容：任务队列积压且有空闲线程容量时，自动新增线程
        with self._worker_lock:
            idle_count = len([w for w in self._workers.values() if w.status == "idle"])
            if self._task_queue.qsize() > idle_count and len(self._workers) < self._max_threads:
                self._start_worker()
        logger.info(
            f"任务投递成功 | ID：{task_id} | 名称：{task_name} | 优先级：{_priority} | 队列积压：{self._task_queue.qsize()}")
        return task_id

    def submit_batch(
            self,
            task_list: List[Tuple[Callable[..., Any], tuple, dict]],
            task_name_prefix: str = "batch-task",
            **kwargs
    ) -> List[str]:
        """
        批量投递任务
        :param task_list: 任务列表，每个元素为(func, args, kwargs)
        :param task_name_prefix: 批量任务名前缀
        :param kwargs: 公共参数（priority/max_retry/retry_interval/timeout/callback）
        :return: 任务ID列表
        """
        task_ids = []
        for idx, (func, args, task_kwargs) in enumerate(task_list):
            task_name = f"{task_name_prefix}-{idx + 1}"
            tid = self.submit_task(func, *args, task_name=task_name, **kwargs, **task_kwargs)
            task_ids.append(tid)
        logger.info(f"批量任务投递完成 | 总数：{len(task_ids)} | 队列积压：{self._task_queue.qsize()}")
        return task_ids

    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """查询单个任务信息"""
        with self._task_lock:
            return self._task_map.get(task_id)

    def get_all_task_info(self, status: Optional[TaskStatus] = None) -> List[TaskInfo]:
        """
        查询所有任务信息，支持按状态过滤
        :param status: 任务状态（None=返回所有）
        :return: 任务信息列表
        """
        with self._task_lock:
            if status:
                return [t for t in self._task_map.values() if t.status == status]
            return list(self._task_map.values())

    def cancel_task(self, task_id: str, force: bool = False) -> bool:
        """
        取消任务（高效实现，无需遍历队列）
        :param task_id: 任务ID
        :param force: 是否强制取消（即使任务正在运行，仅标记状态，无法终止执行）
        :return: 取消成功返回True
        """
        if self._stop_event.is_set():
            raise RuntimeError("线程池已销毁，无法取消任务")

        with self._task_lock:
            task = self._task_map.get(task_id)
            if not task:
                logger.warning(f"取消任务失败：{task_id} 不存在")
                return False
            if task.status in ["success", "failed", "cancelled"]:
                logger.warning(f"取消任务失败：{task_id} 状态为 {task.status}，无需取消")
                return False
            if task.status == "running" and not force:
                logger.warning(f"取消任务失败：{task_id} 正在运行（非强制模式）")
                return False
            # 仅标记状态，消费时判断（高效取消，适合大队列）
            task.status = "cancelled"
            self._task_map[task_id] = task
        logger.info(f"任务取消成功 | ID：{task_id} | 名称：{task.task_name} | 原状态：{task.status}")
        return True

    def cancel_all_tasks(self, force: bool = False) -> int:
        """
        取消所有任务
        :param force: 是否强制取消运行中的任务
        :return: 成功取消的任务数
        """
        if self._stop_event.is_set():
            raise RuntimeError("线程池已销毁，无法取消任务")

        cancel_count = 0
        with self._task_lock:
            for task in self._task_map.values():
                if task.status in ["pending", "retrying"] or (force and task.status == "running"):
                    task.status = "cancelled"
                    cancel_count += 1
        logger.info(f"批量取消任务完成 | 成功取消：{cancel_count} | 队列积压：{self._task_queue.qsize()}")
        return cancel_count

    # ------------------------------ 核心功能：线程管理 ------------------------------
    def adjust_thread_num(self, target_num: int) -> int:
        """
        动态调整工作线程数
        :param target_num: 目标线程数（需在1~max_threads之间）
        :return: 调整后的实际线程数
        """
        if self._stop_event.is_set():
            raise RuntimeError("线程池已销毁，无法调整线程数")
        with self._worker_lock:
            current_num = len(self._workers)
            target_num = max(1, min(target_num, self._max_threads))
            if target_num == current_num:
                logger.info(f"线程数无需调整 | 当前：{current_num} | 目标：{target_num}")
                return current_num
            # 扩容
            if target_num > current_num:
                need_add = target_num - current_num
                for _ in range(need_add):
                    self._start_worker()
            # 缩容（仅移除空闲线程）
            else:
                need_remove = current_num - target_num
                idle_workers = [name for name, info in self._workers.items() if info.status == "idle"]
                for name in idle_workers[:need_remove]:
                    self._remove_worker(name)
            final_num = len(self._workers)
        logger.info(f"线程数调整完成 | 原数：{current_num} | 目标：{target_num} | 实际：{final_num}")
        return final_num

    def get_worker_info(self) -> Dict[str, WorkerInfo]:
        """获取所有工作线程信息"""
        with self._worker_lock:
            return self._workers.copy()

    def get_thread_stats(self) -> Dict[str, Any]:
        """获取线程池统计信息（便于监控）"""
        with self._worker_lock:
            total = len(self._workers)
            running = len([w for w in self._workers.values() if w.status == "running"])
            idle = total - running
        with self._task_lock:
            task_total = len(self._task_map)
            task_running = len([t for t in self._task_map.values() if t.status == "running"])
            task_pending = len([t for t in self._task_map.values() if t.status in ["pending", "retrying"]])
        return {
            "thread": {"total": total, "running": running, "idle": idle, "max": self._max_threads},
            "task": {"total": task_total, "running": task_running, "pending": task_pending,
                     "queue_size": self._task_queue.qsize()},
            "status": "stopped" if self._stop_event.is_set() else "running" if not self._pause_event.is_set() else "paused"
        }

    # ------------------------------ 核心功能：状态控制 ------------------------------
    def pause(self):
        """暂停线程池（新任务可投递，队列积压，不执行）"""
        if not self._pause_event.is_set():
            self._pause_event.set()
            logger.info("线程池已暂停 | 任务队列将继续积压")

    def resume(self):
        """恢复线程池"""
        if self._pause_event.is_set():
            self._pause_event.clear()
            logger.info("线程池已恢复 | 开始执行队列中的任务")

    def set_task_callback(self, callback: TaskCallback):
        """设置全局任务完成回调"""
        with self._config_lock:
            self._global_task_callback = callback
        logger.info("全局任务完成回调已更新")

    def update_config(
            self,
            **kwargs
    ):
        """
        更新全局配置（支持动态修改）
        :param kwargs: 配置项（idle_recycle_seconds/default_priority/default_max_retry/default_retry_interval）
        """
        with self._config_lock:
            for k, v in kwargs.items():
                if k in self._config:
                    self._config[k] = v
        logger.info(f"线程池全局配置已更新 | 新配置：{kwargs}")

    def destroy(self, wait_tasks_done: bool = True, timeout: Optional[float] = None):
        """
        销毁线程池（资源全清理，不可逆）
        :param wait_tasks_done: 是否等待任务完成
        :param timeout: 等待超时时间(秒)，None=无限等待
        """
        if self._stop_event.is_set():
            logger.info("线程池已销毁，无需重复操作")
            return
        logger.info(
            f"开始销毁线程池 | 等待任务完成：{wait_tasks_done} | 超时：{timeout} | 当前统计：{self.get_thread_stats()}")

        # 标记停止，恢复暂停，让线程退出
        self._stop_event.set()
        self._pause_event.clear()

        # 等待任务队列完成（带超时）
        start_time = time.time()
        if wait_tasks_done and not self._task_queue.empty():
            try:
                while not self._task_queue.empty():
                    if timeout and (time.time() - start_time) > timeout:
                        logger.warning(
                            f"等待任务完成超时（{timeout}秒），剩余任务将被终止 | 队列剩余：{self._task_queue.qsize()}")
                        break
                    # join 在 Python 标准库中没有 timeout 参数，这里只做短暂 sleep + 状态检查
                    self._task_queue.join()
            except Exception as e:
                logger.error(f"等待任务完成异常：{str(e)}", exc_info=True)

        # 等待工作线程退出
        worker_names = list(self._workers.keys())
        for name in worker_names:
            with self._worker_lock:
                worker = self._workers.get(name)
                if not worker or not worker.thread.is_alive():
                    continue
            # 计算剩余超时时间
            remaining = None
            if timeout:
                elapsed = time.time() - start_time
                remaining = max(timeout - elapsed, 0)
                if remaining <= 0:
                    break
            try:
                worker.thread.join(timeout=remaining)
                logger.info(f"工作线程已正常退出：{name}")
            except RuntimeError as e:
                logger.error(f"等待线程{name}退出异常：{str(e)}", exc_info=True)

        # 将未完成的任务标记为 cancelled，并回调通知（优雅停止）
        with self._task_lock:
            now = time.time()
            pending_tasks: List[TaskInfo] = []
            for task in self._task_map.values():
                if task.status not in ("success", "failed", "cancelled"):
                    task.status = "cancelled"
                    task.end_time = now
                    pending_tasks.append(task)
            for task in pending_tasks:
                logger.info(f"销毁时取消任务 | ID：{task.task_id} | 名称：{task.task_name} | 原状态：{task.status}")
                self._execute_task_callback(task)
            # 清空任务映射
            self._task_map.clear()
        with self._worker_lock:
            self._workers.clear()
        # 清空队列（避免内存泄漏）
        while not self._task_queue.empty():
            self._task_queue.get()
            self._task_queue.task_done()

        logger.info("线程池销毁完成 | 所有资源已清理")

    # ------------------------------ 上下文管理器：支持with语句 ------------------------------
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"线程池执行异常：{exc_val}", exc_info=True)
        self.destroy(wait_tasks_done=True, timeout=30)

    # ------------------------------ 兼容原中文命名方法 ------------------------------
    def 创建(self, num_threads: int) -> "DarrenThreadPool":
        return self.__class__(num_threads)

    def 投递任务(self, *args, **kwargs) -> str:
        return self.submit_task(*args, **kwargs)

    def 批量投递(self, *args, **kwargs) -> List[str]:
        return self.submit_batch(*args, **kwargs)

    def 取任务信息(self, *args, **kwargs) -> Optional[TaskInfo]:
        return self.get_task_info(*args, **kwargs)

    def 取所有任务信息(self, *args, **kwargs) -> List[TaskInfo]:
        return self.get_all_task_info(*args, **kwargs)

    def 取消任务(self, *args, **kwargs) -> bool:
        return self.cancel_task(*args, **kwargs)

    def 取消所有任务(self, *args, **kwargs) -> int:
        return self.cancel_all_tasks(*args, **kwargs)

    def 调整线程数(self, *args, **kwargs) -> int:
        return self.adjust_thread_num(*args, **kwargs)

    def 取线程统计(self, *args, **kwargs) -> Dict[str, Any]:
        return self.get_thread_stats(*args, **kwargs)

    def 取线程总数(self) -> int:
        with self._worker_lock:
            return len(self._workers)

    def 取正在执行数(self) -> int:
        return self.get_thread_stats()["task"]["running"]

    def 取空闲线程数(self) -> int:
        return self.get_thread_stats()["thread"]["idle"]

    def 取是否空闲(self) -> bool:
        stats = self.get_thread_stats()
        return stats["task"]["running"] == 0 and stats["task"]["queue_size"] == 0

    def 暂停(self):
        self.pause()

    def 恢复(self):
        self.resume()

    def 设置回调(self, *args, **kwargs):
        self.set_task_callback(*args, **kwargs)

    def 更新配置(self, *args, **kwargs):
        self.update_config(*args, **kwargs)

    def 销毁(self, *args, **kwargs):
        self.destroy(*args, **kwargs)

    # ------------------------------ 析构函数：兜底清理 ------------------------------
    def __del__(self):
        if not self._stop_event.is_set():
            self.destroy(wait_tasks_done=False, timeout=10)
            logger.warning("线程池未手动销毁，析构函数自动兜底清理（建议使用with语句）")


# ------------------------------ 测试示例 ------------------------------
if __name__ == "__main__":
    def test_task(num: int, sleep: float = 1.0):
        """测试任务函数"""
        time.sleep(sleep)
        if num % 3 == 0:
            raise ValueError(f"测试异常：num={num}（能被3整除）")
        return f"success-num-{num}"


    def test_callback(task: TaskInfo):
        """测试任务回调"""
        logger.info(f"【任务回调】ID：{task.task_id} | 状态：{task.status} | 结果：{task.result}")


    # 1. 上下文管理器方式使用（推荐，自动销毁）
    with DarrenThreadPool(
            num_threads=2,
            max_threads=5,
            min_idle_threads=1,
            idle_recycle_seconds=10,
            task_done_callback=test_callback
    ) as pool:
        # 2. 投递单个任务
        tid1 = pool.submit_task(test_task, 1, sleep=0.5, task_name="单任务-1")
        # 3. 投递带局部回调的任务
        tid2 = pool.submit_task(test_task, 3, sleep=0.5, task_name="单任务-2（无重试）", callback=test_callback)
        # 4. 批量投递任务
        batch_tasks = [
            (test_task, (5,), {"sleep": 0.5}),
            (test_task, (6,), {"sleep": 0.5}),
            (test_task, (7,), {"sleep": 0.5, "priority": 10})
        ]
        batch_tids = pool.submit_batch(batch_tasks, task_name_prefix="批量任务", timeout=3)

        # 5. 动态调整线程数
        pool.adjust_thread_num(4)

        # 6. 取消一个未执行的批量任务
        if batch_tids:
            pool.cancel_task(batch_tids[-1])

        # 7. 打印线程池统计信息
        for _ in range(5):
            time.sleep(0.5)
            logger.info(f"【线程池统计】{pool.get_thread_stats()}")

        # 8. 查询任务信息
        all_tasks = pool.get_all_task_info()
        logger.info(f"【所有任务】总数：{len(all_tasks)} | 待执行：{len(pool.get_all_task_info('pending'))}")

        # 等待所有任务执行完成
        time.sleep(5)

    # 测试完成，with语句结束后自动销毁线程池
    logger.info("测试完成，线程池已自动销毁")