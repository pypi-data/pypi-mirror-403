import os
import time
import pytest

from ddtols import init, log_execution, timer

@pytest.fixture(autouse=True)
def setup_module():
    init()

def test_timer_decorator(capsys):
    """
    测试 timer 装饰器是否能正常工作并打印耗时。
    capsys 是 pytest 的一个夹具，用来捕获标准输出（print的内容）。
    """
    
    # 1. 定义一个被装饰的函数
    @timer
    def slow_func():
        time.sleep(0.1)
        return "done"
    
    # 2. 执行函数
    result = slow_func()
    
    # 3. 验证返回值是否正确（装饰器不应该改变原有逻辑）
    assert result == "done"
    
    # 4. 验证是否有打印输出
    captured = capsys.readouterr()
    # 期望输出包含 "执行耗时" 和 "秒"
    assert "执行耗时" in captured.out
    assert "秒" in captured.out
    assert "slow_func" in captured.out

def test_log_execution_decorator():
    """
    测试 log_execution 装饰器是否能记录参数和返回值。
    注意：通过检查日志文件来验证。
    """
    
    # 1. 定义被装饰函数
    @log_execution
    def add(a, b):
        return a + b
    
    # 2. 执行函数
    result = add(10, 20)
    
    # 3. 验证返回值
    assert result == 30
    
    # 4. 验证日志输出（通过文件）
    # 日志文件在 logs 目录下
    log_file = os.path.join("logs", "ddtols.log")
    assert os.path.exists(log_file)
    
    with open(log_file, encoding="utf-8") as f:
        log_text = f.read()
        
    assert "开始执行" in log_text
    assert "函数名=add" in log_text
    assert "参数=(10, 20)" in log_text
    assert "执行结束" in log_text
    assert "状态=成功" in log_text
    assert "结果=30" in log_text

def test_log_execution_exception():
    """
    测试 log_execution 在函数报错时是否能捕获并打印错误信息。
    """
    @log_execution
    def fail_func():
        raise ValueError("Oops!")
    
    # 验证是否抛出了异常
    with pytest.raises(ValueError):
        fail_func()
    
    # 验证错误日志
    log_file = os.path.join("logs", "ddtols.log")
    with open(log_file, encoding="utf-8") as f:
        log_text = f.read()
        
    assert "执行结束" in log_text
    assert "状态=失败" in log_text
    assert "错误=ValueError: Oops!" in log_text
