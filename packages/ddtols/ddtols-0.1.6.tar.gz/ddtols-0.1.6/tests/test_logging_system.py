import logging
import os
import shutil

import pytest

from ddtols import AESCipher, init, log_execution, write_log

@pytest.fixture
def clean_logs():
    """
    清理日志目录。
    """
    logging.shutdown()
    dirs_to_clean = ["logs", "test_logs"]
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

def test_init_creates_log_file(clean_logs):
    """测试初始化是否创建日志文件"""
    log_dir = "test_logs"
    init(log_dir=log_dir)
    
    assert os.path.exists(log_dir)
    assert os.path.exists(os.path.join(log_dir, "ddtols.log"))

def test_core_logging(clean_logs):
    """测试核心函数是否记录日志"""
    log_dir = "test_logs"
    # 将日志级别设为 DEBUG，确保更详细的日志也可以被写入（如果业务代码有 debug 日志）。
    
    init(log_dir=log_dir, level=logging.DEBUG)
    
    # 手动写入一条
    write_log("Manual log entry")
    
    log_file = os.path.join(log_dir, "ddtols.log")
    with open(log_file, encoding="utf-8") as f:
        content = f.read()
        assert "Manual log entry" in content
        assert "[INFO] [ddtols.legacy]" in content

def test_decorator_logging(clean_logs):
    """测试装饰器是否记录日志"""
    log_dir = "test_logs"
    init(log_dir=log_dir)
    
    @log_execution
    def my_func(x):
        return x * 2
        
    my_func(10)
    
    log_file = os.path.join(log_dir, "ddtols.log")
    with open(log_file, encoding="utf-8") as f:
        content = f.read()
        # 适配新的日志格式
        assert "开始执行" in content
        assert "函数名=my_func" in content
        assert "参数=(10)" in content
        assert "执行结束" in content
        assert "状态=成功" in content
        assert "结果=20" in content
        assert "耗时=" in content

def test_enforce_init():
    """测试未初始化报错"""
    # 这里的关键是确保 _INITIALIZED 为 False
    # 但由于 pytest 可能会并发或重用，我们需要重置状态
    import ddtols.main
    ddtols.main._INITIALIZED = False
    
    with pytest.raises(RuntimeError, match="not initialized"):
        AESCipher(b"1234567812345678")
        
    with pytest.raises(RuntimeError, match="not initialized"):
        write_log("test")

    # 恢复初始化以免影响其他测试（虽然 fixture 会清理文件，但内存状态要注意）
    init()
