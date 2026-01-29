import logging
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional
from enum import Enum, auto

# 尝试获取项目内部的 diary 模块，如果失败则使用标准 logging
try:
    from .diary import get_logger
    _default_logger = get_logger(__name__)
except ImportError:
    _default_logger = logging.getLogger(__name__)


class SchedulerStatus(Enum):
    """Scheduler 的运行状态枚举"""
    IDLE = auto()       # 空闲/未开始
    RUNNING = auto()    # 正在运行
    COMPLETED = auto()  # 全部完成
    FAILED = auto()     # 发生错误并停止
    STOPPED = auto()    # 手动停止（预留）


@dataclass
class Task:
    """
    任务数据类，内部使用，用于封装待执行的任务信息。

    Attributes:
        func (Callable[..., Any]): 要执行的函数或可调用对象。
        args (tuple): 传递给函数的位置参数元组。
        kwargs (dict): 传递给函数的关键字参数字典。
        name (str): 任务名称，用于日志记录。
    """
    func: Callable[..., Any]
    args: tuple
    kwargs: dict
    name: str


class Scheduler:
    """
    简单任务调度器类。

    允许用户按顺序添加多个任务（函数及其参数），然后通过启动方法依次执行这些任务。
    适用于需要按特定步骤执行一系列操作的场景。
    """

    def __init__(
        self, 
        name: str | None = None, 
        stop_on_error: bool = True,
        signal_handler: Callable[[str, dict], None] | None = None
    ) -> None:
        """
        初始化调度器对象。

        Args:
            name (str, optional):
                调度器名称，用于设置日志记录器的名称。
                如果提供，日志名称将为 'ddtols.<name>' (取决于 get_logger 实现)。
                如果不提供，使用默认模块日志 'ddtols.scheduler'。
            stop_on_error (bool, optional): 
                错误处理策略。
                如果为 True（默认值），当某个任务执行抛出异常时，调度器会立即停止，不再执行后续任务，并向上抛出该异常。
                如果为 False，当某个任务出错时，会记录错误日志，但继续尝试执行后续的任务。
            signal_handler (Callable[[str, dict], None], optional):
                信号回调函数，用于接收调度器的事件通知。
                回调签名：(event_type: str, data: dict) -> None
                事件类型包括：
                - "start": 调度器启动 (data: total_tasks)
                - "task_start": 任务开始 (data: task_name, index, total)
                - "task_success": 任务成功 (data: task_name, result)
                - "task_error": 任务出错 (data: task_name, error)
                - "finish": 调度器完成 (data: results, status)
        """
        self._tasks: List[Task] = []
        self.stop_on_error = stop_on_error
        self.status = SchedulerStatus.IDLE
        self.current_index = -1
        self.signal_handler = signal_handler
        self._stop_requested = False
        
        if name:
            try:
                from .diary import get_logger
                self.logger = get_logger(name)
            except ImportError:
                self.logger = logging.getLogger(name)
        else:
            self.logger = _default_logger
            
        self.logger.debug("Scheduler initialized. Name: %s, Stop on error: %s", name, stop_on_error)

    def _emit_signal(self, event: str, **kwargs: Any) -> None:
        """内部方法：触发信号回调"""
        if self.signal_handler:
            try:
                self.signal_handler(event, kwargs)
            except Exception as e:
                self.logger.error("Error in signal handler: %s", e)

    def add(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """
        向调度器添加一个待执行的任务。

        该方法会将函数及其参数封装为一个任务对象，并加入到执行队列的末尾。

        Args:
            func (Callable[..., Any]): 
                要执行的目标函数或方法。可以是任何可调用对象。
            *args (Any): 
                传递给目标函数的位置参数（Positional Arguments）。
                例如：scheduler.add(my_func, 1, 2) 中的 1 和 2。
            **kwargs (Any): 
                传递给目标函数的关键字参数（Keyword Arguments）。
                例如：scheduler.add(my_func, param="value") 中的 param="value"。
        
        Returns:
            None
        """
        # 获取函数名称用于日志记录，如果是 lambda 或 partial 可能没有 __name__
        task_name = getattr(func, "__name__", str(func))
        
        # 创建任务对象
        task = Task(func=func, args=args, kwargs=kwargs, name=task_name)
        self._tasks.append(task)
        self.logger.debug("Task added to scheduler: %s", task_name)

    def start(self, stop_on_error: bool | None = None) -> List[Any]:
        """
        启动调度器，按添加顺序依次执行所有任务。

        Args:
            stop_on_error (bool | None, optional):
                本次执行的错误处理策略。
                如果提供（True 或 False），将覆盖初始化时的 stop_on_error 设置。
                如果为 None（默认），则使用初始化时的配置。

        Returns:
            List[Any]: 
                包含所有成功执行任务返回值的列表。
                列表中的元素顺序与任务添加顺序一致。
                如果某个任务没有返回值（返回 None），列表中也会包含 None。

        Raises:
            Exception: 
                如果最终生效的 stop_on_error 为 True，当任何任务抛出异常时，
                该异常会被重新抛出，且后续任务不会被执行。
        """
        results: List[Any] = []
        total_tasks = len(self._tasks)
        
        # 确定本次执行的错误处理策略
        current_stop_on_error = stop_on_error if stop_on_error is not None else self.stop_on_error
        
        self.logger.info("Scheduler started. Total tasks: %d. Stop on error: %s", total_tasks, current_stop_on_error)
        
        self.status = SchedulerStatus.RUNNING
        self._stop_requested = False
        self._emit_signal("start", total_tasks=total_tasks)

        for index, task in enumerate(self._tasks):
            # 检查是否请求停止
            if self._stop_requested:
                self.logger.warning("Scheduler stopped by user request.")
                self.status = SchedulerStatus.STOPPED
                self._emit_signal("finish", results=results, status=self.status)
                return results

            # 记录当前执行进度，index 从 0 开始，显示时 +1
            self.current_index = index
            step_info = f"[{index + 1}/{total_tasks}]"
            self.logger.info("%s Executing task: %s", step_info, task.name)
            
            self._emit_signal("task_start", task_name=task.name, index=index, total=total_tasks)

            try:
                # 执行任务并获取返回值
                # *task.args 解包位置参数
                # **task.kwargs 解包关键字参数
                result = task.func(*task.args, **task.kwargs)
                results.append(result)
                self.logger.debug("%s Task finished successfully.", step_info)
                self._emit_signal("task_success", task_name=task.name, result=result)
            
            except Exception as e:
                # 捕获任务执行过程中的异常
                self.logger.error("%s Task '%s' failed with error: %s", step_info, task.name, e)
                self._emit_signal("task_error", task_name=task.name, error=e)
                
                if current_stop_on_error:
                    self.logger.critical("Scheduler stopping due to error in task: %s", task.name)
                    self.status = SchedulerStatus.FAILED
                    self._emit_signal("finish", results=results, status=self.status)
                    raise  # 重新抛出异常，中断执行
                else:
                    # 如果配置为不停止，则记录结果为 None（或者可以考虑记录异常对象）
                    # 这里为了保持结果列表长度一致，我们追加 None，或者可以考虑追加异常对象本身以便调用者检查
                    self.logger.warning("Continuing execution despite error...")
                    results.append(None) 

        self.status = SchedulerStatus.COMPLETED
        self.logger.info("All tasks execution completed.")
        self._emit_signal("finish", results=results, status=self.status)
        return results

    def stop(self) -> None:
        """
        请求停止调度器。
        
        调度器将在当前正在执行的任务完成后停止，不再执行后续任务。
        状态将变为 STOPPED。
        """
        if self.status == SchedulerStatus.RUNNING:
            self._stop_requested = True
            self.logger.info("Stop requested. Scheduler will stop after current task.")
        else:
            self.logger.warning("Scheduler is not running, stop request ignored.")

    def configure(
        self, 
        stop_on_error: bool | None = None,
        signal_handler: Callable[[str, dict], None] | None = None
    ) -> None:
        """
        在初始化后动态配置调度器参数。
        
        Args:
            stop_on_error (bool, optional): 更新错误处理策略。
            signal_handler (Callable, optional): 更新信号回调函数。
        """
        if stop_on_error is not None:
            self.stop_on_error = stop_on_error
        if signal_handler is not None:
            self.signal_handler = signal_handler
        self.logger.debug("Scheduler configured. Stop on error: %s, Handler updated: %s", 
                          self.stop_on_error, signal_handler is not None)

    def clear(self) -> None:
        """
        清空调度器中所有待执行的任务。
        
        Args:
            None
        """
        count = len(self._tasks)
        self._tasks.clear()
        self.status = SchedulerStatus.IDLE
        self.current_index = -1
        self.logger.info("Scheduler cleared. Removed %d tasks.", count)
