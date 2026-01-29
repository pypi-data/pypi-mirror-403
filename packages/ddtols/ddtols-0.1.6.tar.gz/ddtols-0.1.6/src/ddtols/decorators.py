import datetime
import functools
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar, cast, overload

# 导入新的日志获取函数
from .diary import get_logger

P = ParamSpec("P")
R = TypeVar("R")

def timer(func: Callable[P, R]) -> Callable[P, R]:
    """
    一个用于计算函数执行时间的装饰器。
    
    当你把这个装饰器放在一个函数上面时，它会自动记录函数开始执行和
    结束执行的时间，并计算出总耗时，最后打印出来，并记录到日志中。
    非常适合用来检查代码的性能瓶颈。

    参数：
    func (Callable): 需要被装饰的目标函数。

    返回：
    Callable: 已经被包装好的新函数，它在执行原函数逻辑的同时会计算时间。
    
    使用示例：
    @timer
    def my_slow_function():
        time.sleep(1)
    """
    logger = get_logger("decorators.timer")
    
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """
        这是内部的包装函数，它会替代原函数被执行。
        
        参数：
        *args: 传递给原函数的位置参数（例如：1, 2, "a"）。
        **kwargs: 传递给原函数的关键字参数（例如：name="Alice", age=18）。
        
        返回：
        Any: 原函数的返回值。
        """
        # 1. 记录开始时间（使用 perf_counter 获取高精度时间）
        start_time = time.perf_counter()
        
        try:
            # 2. 执行原函数，并获取返回值
            return func(*args, **kwargs)
        finally:
            # 3. 无论原函数是否报错，都记录结束时间
            end_time = time.perf_counter()
            
            # 4. 计算耗时（秒）
            elapsed_time = end_time - start_time
            
            msg = f"函数 [{func.__name__}] 执行耗时: {elapsed_time:.4f} 秒"
            # 5. 打印耗时信息并记录日志
            print(msg)
            logger.info(msg)
            
    return cast(Callable[P, R], wrapper)

@overload
def log_execution(func: Callable[P, R]) -> Callable[P, R]: ...

@overload
def log_execution(*, max_result_length: int = 1000) -> Callable[[Callable[P, R]], Callable[P, R]]: ...

def log_execution(
    func: Callable[P, R] | None = None,
    *,
    max_result_length: int = 1000
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """
    一个用于记录函数调用详细日志的装饰器。
    
    功能：
    - 记录函数开始时间、函数名、参数
    - 记录函数执行结果（返回值）
    - 记录函数执行耗时
    - 捕获并记录异常信息
    - 支持限制结果字符串长度，避免日志过大
    
    使用标准日志系统输出。
    
    参数：
    func (Callable): 需要被记录日志的目标函数。
    max_result_length (int): 结果字符串的最大长度，默认为 1000。超过此长度将被截断。

    返回：
    Callable: 包装后的新函数。
    """
    
    def actual_decorator(f: Callable[P, R]) -> Callable[P, R]:
        logger = get_logger("decorators.log_execution")
        
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # 1. 准备调用信息
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            
            # 获取当前可读时间
            start_dt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            start_msg = (
                f"开始执行: "
                f"函数名={f.__name__}, "
                f"时间={start_dt}, "
                f"参数=({signature})"
            )
            logger.info(start_msg)
            
            # 计时
            start_perf = time.perf_counter()
            
            try:
                # 2. 执行函数
                result = f(*args, **kwargs)
                
                # 3. 计算耗时
                end_perf = time.perf_counter()
                duration = end_perf - start_perf
                
                # 处理结果字符串长度
                result_repr = repr(result)
                if len(result_repr) > max_result_length:
                    result_repr = result_repr[:max_result_length] + "..."
                
                end_msg = (
                    f"执行结束: "
                    f"函数名={f.__name__}, "
                    f"状态=成功, "
                    f"耗时={duration:.4f}秒, "
                    f"结果={result_repr}"
                )
                logger.info(end_msg)
                return result
                
            except Exception as e:
                # 4. 处理异常
                end_perf = time.perf_counter()
                duration = end_perf - start_perf
                
                error_msg = (
                    f"执行结束: "
                    f"函数名={f.__name__}, "
                    f"状态=失败, "
                    f"耗时={duration:.4f}秒, "
                    f"错误={type(e).__name__}: {str(e)}"
                )
                logger.exception(error_msg)
                raise
                
        return cast(Callable[P, R], wrapper)

    if func is None:
        return actual_decorator
    else:
        return actual_decorator(func)

def log_to_diary(filename: str | None = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    注意：在新的日志系统中，log_to_diary 的行为已调整。
    它不再创建单独的文件，而是作为一个特殊的日志记录器，记录更详细的信息。
    filename 参数目前被忽略，保留是为了兼容性。
    建议改用 log_execution。
    """
    logger = get_logger("decorators.log_to_diary")
    
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # 1. 准备调用信息
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            
            # 2. 记录开始执行
            logger.info(f"调用函数: {func.__name__}, 参数: ({signature})")
            
            try:
                # 3. 执行原函数
                result = func(*args, **kwargs)
                
                # 4. 记录执行成功及返回值
                logger.info(f"函数 {func.__name__} 执行成功, 返回值: {result!r}")
                
                return result
            except Exception as e:
                # 5. 记录执行异常
                msg = (
                    f"函数 {func.__name__} 执行出错! "
                    f"错误类型: {type(e).__name__}, "
                    f"错误信息: {str(e)}"
                )
                logger.exception(
                    msg
                )
                raise
                
        return cast(Callable[P, R], wrapper)
    return decorator
