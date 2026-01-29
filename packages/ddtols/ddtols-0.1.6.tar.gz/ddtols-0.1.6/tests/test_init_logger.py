import logging
import os
import shutil
import pytest

from ddtols import init, write_log

@pytest.fixture
def clean_dirs():
    """
    清理测试中生成的目录。
    """
    logging.shutdown()
    dirs_to_clean = ["logs", "custom_logs"]
    for d in dirs_to_clean:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
            except PermissionError:
                pass
    yield
    logging.shutdown()
    for d in dirs_to_clean:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
            except PermissionError:
                pass

def test_init_logger_default(clean_dirs):
    """
    测试不传参数时，默认在当前目录创建 logs 文件夹。
    """
    # 1. 初始化（不传参）
    init()
    
    # 2. 写入日志
    write_log("Testing default init")
    
    # 3. 验证是否在 logs 目录下生成文件
    expected_dir = os.path.join(os.getcwd(), "logs")
    assert os.path.exists(expected_dir)
    # 验证日志文件是否存在（ddtols.log）
    log_file = os.path.join(expected_dir, "ddtols.log")
    assert os.path.exists(log_file)

def test_init_logger_custom(clean_dirs):
    """
    测试传入自定义路径时，在指定位置创建文件夹。
    """
    custom_dir = os.path.abspath("custom_logs")
    
    # 1. 初始化（传参）
    init(log_dir=custom_dir)
    
    # 2. 写入日志
    write_log("Testing custom init")
    
    # 3. 验证目录
    assert os.path.exists(custom_dir)
    
    # 4. 验证文件内容
    # 只需要找目录下任意一个 .log 文件 (ddtols.log)
    files = os.listdir(custom_dir)
    log_files = [f for f in files if f.endswith(".log") or "ddtols" in f]
    assert len(log_files) > 0

def test_init_logger_switching(clean_dirs):
    """
    测试运行中切换目录。
    """
    # 1. 先用默认
    init()
    write_log("Log 1")
    assert os.path.exists("logs")
    
    # 2. 切换到自定义
    init("custom_logs")
    write_log("Log 2")
    assert os.path.exists("custom_logs")
    
    # 3. 验证两个目录都生成了日志文件
    assert os.path.exists(os.path.join("logs", "ddtols.log"))
    assert os.path.exists(os.path.join("custom_logs", "ddtols.log"))
