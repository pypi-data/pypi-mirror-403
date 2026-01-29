import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# 定义库的根 Logger 名称
LIBRARY_LOGGER_NAME = "ddtols"

_root_logger = logging.getLogger(LIBRARY_LOGGER_NAME)
if not _root_logger.handlers:
    _root_logger.addHandler(logging.NullHandler())

def setup_logging(
    log_dir: str,
    level: int = logging.INFO,
    add_console: bool = True,
    propagate: bool = False,
    clear_handlers: bool = True,
) -> None:
    """
    配置 ddtols 的全局日志系统。
    
    功能：
    1. 确保日志目录存在。
    2. 配置 Logger 输出到控制台 (StreamHandler)。
    3. 配置 Logger 输出到文件 (TimedRotatingFileHandler)，每天轮转一次。
    4. 设置统一的日志格式。

    参数：
    log_dir (str): 日志存储目录。
    level (int): 日志级别，默认为 logging.INFO。
    add_console (bool): 是否输出到控制台，默认 True。
    propagate (bool): 是否向上游传播日志，默认 False。
    clear_handlers (bool): 是否清理旧 handlers，默认 True。
    """
    # 1. 准备目录
    log_path = Path(log_dir)
    if not log_path.exists():
        log_path.mkdir(parents=True, exist_ok=True)
        
    # 2. 获取库的根 Logger
    logger = logging.getLogger(LIBRARY_LOGGER_NAME)
    logger.setLevel(level)
    
    # 清理旧的 handlers，防止重复添加（例如多次调用 init）
    if clear_handlers and logger.handlers:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass
        
    # 禁止日志向上传播，防止被父级 logger（如 root）重复记录
    logger.propagate = propagate
    
    # 3. 定义日志格式
    # 格式：[时间] [级别] [模块名] 消息
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 4. 添加控制台 Handler
    if add_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)
    
    # 5. 添加文件 Handler (按天轮转)
    # 文件名：ddtols.log，会自动轮转为 ddtols.log.2023-10-27
    log_file = log_path / "ddtols.log"
    file_handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",      # 每天午夜轮转
        interval=1,           # 间隔 1 天
        backupCount=30,       # 保留最近 30 天
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized. Log directory: {log_path.absolute()}")

def get_logger(name: str | None = None) -> logging.Logger:
    """
    获取 ddtols 库下的子 Logger。
    
    参数：
    name (str, optional): 子模块名称。如果不传，返回根 logger。
                          如果传入 "core"，返回 "ddtols.core"。
    
    返回：
    logging.Logger: 配置好的 Logger 对象。
    """
    if name:
        # 确保子 logger 是 ddtols 的后代
        if not name.startswith(LIBRARY_LOGGER_NAME + "."):
            logger_name = f"{LIBRARY_LOGGER_NAME}.{name}"
        else:
            logger_name = name
    else:
        logger_name = LIBRARY_LOGGER_NAME
        
    return logging.getLogger(logger_name)

# 为了兼容旧代码的 write_log 接口（虽然现在建议直接用 logger）
def write_log_legacy(content: str, level: int = logging.INFO) -> None:
    """
    兼容旧版接口的日志写入函数。
    注意：不再支持自定义 filename，统一由 logging 模块管理文件。
    """
    logger = get_logger("legacy")
    logger.log(level, content)
