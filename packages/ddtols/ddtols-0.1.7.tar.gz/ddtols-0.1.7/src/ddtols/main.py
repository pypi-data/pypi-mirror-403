"""
ddtols 主入口模块。

这个模块汇聚了库中所有的核心功能，并实现了全局初始化控制。
必须先调用 init() 方法，才能使用其他功能。
"""

import functools
import logging
import os
from collections.abc import Callable
from typing import Any, TypeVar, cast
from .cipher import (
    AESCipher as _AESCipher,
    RSACipher as _RSACipher
)
from .decorators import (
    log_execution as _log_execution,
    log_to_diary as _log_to_diary,
    timer as _timer,
)
from .diary import setup_logging as _setup_logging, write_log_legacy as _write_log_legacy
from .jsenv import JSEnv as _JSEnv
from .scheduler import Scheduler as _Scheduler, SchedulerStatus

# --- 全局状态控制 ---

_INITIALIZED = False

def init(log_dir: str | None = None, level: int = logging.INFO) -> None:
    """
    初始化 ddtols 库。
    
    在使用库的其他功能之前，必须先调用此方法。
    
    参数：
    log_dir (str, optional): 日志存储目录路径。
                             如果不传，默认在当前工作目录下创建 "logs" 文件夹。
    level (int): 日志级别，默认为 logging.INFO。
    """
    global _INITIALIZED
    
    if log_dir is None:
        log_dir = os.path.join(os.getcwd(), "logs")

    # 调用底层的日志初始化
    _setup_logging(log_dir=log_dir, level=level)
    
    _INITIALIZED = True
    # print("ddtols initialized successfully.")

def _ensure_initialized() -> None:
    """检查是否已初始化，未初始化则抛出异常。"""
    if not _INITIALIZED:
        raise RuntimeError("ddtols library is not initialized. Please call ddtols.init() first.")

# --- 功能包装 (Wrapper) ---

# 泛型定义
F = TypeVar('F', bound=Callable[..., Any])

def _wrap_function(func: F) -> F:
    """包装普通函数，增加初始化检查。"""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        _ensure_initialized()
        return func(*args, **kwargs)
    return cast(F, wrapper)

# 1. Core Functions
# (greet 和 safe_int 已被移除)

# 1.1 Crypto Classes
# 对类进行包装，确保实例化时检查初始化状态
class AESCipher(_AESCipher):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _ensure_initialized()
        super().__init__(*args, **kwargs)

class RSACipher(_RSACipher):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _ensure_initialized()
        super().__init__(*args, **kwargs)
        
    # 静态方法也需要包装，因为可能在未实例化时调用
    @staticmethod
    def generate_keys(key_size: int = 2048) -> tuple[str, str]:
        _ensure_initialized()
        return _RSACipher.generate_keys(key_size)

# 1.2 JS Environment
class JSEnv(_JSEnv):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _ensure_initialized()
        super().__init__(*args, **kwargs)

# 1.3 Scheduler
class Scheduler(_Scheduler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _ensure_initialized()
        super().__init__(*args, **kwargs)

# 2. Diary Functions
# 废弃 DiaryManager 类，只保留兼容接口 write_log
write_log = _wrap_function(_write_log_legacy)

# 3. Decorators
# 装饰器的包装比较特殊：
# 我们希望在应用装饰器时不报错（import阶段），但在被装饰函数执行时报错。

def timer(func: F) -> F:
    """
    包装后的 timer 装饰器。
    """
    # 获取原始装饰器返回的 wrapper
    inner_wrapper = _timer(func)
    
    @functools.wraps(inner_wrapper)
    def protected_wrapper(*args: Any, **kwargs: Any) -> Any:
        _ensure_initialized()
        return inner_wrapper(*args, **kwargs)
        
    return cast(F, protected_wrapper)

def log_execution(func: F) -> F:
    """
    包装后的 log_execution 装饰器。
    """
    inner_wrapper = _log_execution(func)
    
    @functools.wraps(inner_wrapper)
    def protected_wrapper(*args: Any, **kwargs: Any) -> Any:
        _ensure_initialized()
        return inner_wrapper(*args, **kwargs)
        
    return cast(F, protected_wrapper)

def log_to_diary(filename: str | None = None) -> Callable[[F], F]:
    """
    包装后的 log_to_diary 装饰器工厂。
    """
    # 获取原始的装饰器
    original_decorator = _log_to_diary(filename=filename)
    
    def protected_decorator(func: F) -> F:
        # 应用原始装饰器，得到 inner_wrapper
        inner_wrapper = original_decorator(func)
        
        @functools.wraps(inner_wrapper)
        def final_wrapper(*args: Any, **kwargs: Any) -> Any:
            _ensure_initialized()
            return inner_wrapper(*args, **kwargs)
            
        return cast(F, final_wrapper)
        
    return protected_decorator

__all__ = [
    "init",
    "AESCipher",
    "RSACipher",
    "JSEnv",
    "write_log", 
    "timer", 
    "log_execution", 
    "log_to_diary",
    "SchedulerStatus"
]
