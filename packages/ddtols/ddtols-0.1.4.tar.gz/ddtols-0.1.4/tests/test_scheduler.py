import pytest
import ddtols
import logging
from ddtols import Scheduler

# 确保在测试前初始化
@pytest.fixture(autouse=True)
def init_ddtols():
    ddtols.init()

def test_scheduler_basic():
    """测试基本的任务添加和执行"""
    scheduler = Scheduler()
    results = []

    def task_a(x):
        return x * 2

    def task_b(y):
        return y + 10

    scheduler.add(task_a, 5)
    scheduler.add(task_b, y=3)

    execution_results = scheduler.start()

    assert execution_results == [10, 13]

def test_scheduler_stop_on_error():
    """测试 stop_on_error=True (默认)"""
    scheduler = Scheduler(stop_on_error=True)
    
    def task_success():
        return "success"
    
    def task_fail():
        raise ValueError("Oops")
    
    def task_skipped():
        return "skipped"

    scheduler.add(task_success)
    scheduler.add(task_fail)
    scheduler.add(task_skipped)

    with pytest.raises(ValueError, match="Oops"):
        scheduler.start()

def test_scheduler_continue_on_error():
    """测试 stop_on_error=False"""
    scheduler = Scheduler(stop_on_error=False)
    
    def task_success():
        return "success"
    
    def task_fail():
        raise ValueError("Oops")
    
    def task_final():
        return "final"

    scheduler.add(task_success)
    scheduler.add(task_fail)
    scheduler.add(task_final)

    results = scheduler.start()
    
    # 根据实现，出错的任务返回 None
    assert results == ["success", None, "final"]

def test_scheduler_start_override():
    """测试在 start 方法中覆盖 stop_on_error 参数"""
    # 初始化时设置为 Stop (True)
    scheduler = Scheduler(stop_on_error=True)
    
    def task_fail():
        raise ValueError("Oops")
    
    def task_final():
        return "final"

    scheduler.add(task_fail)
    scheduler.add(task_final)
    
    # 在 start 时覆盖为 Continue (False)
    results = scheduler.start(stop_on_error=False)
    assert results == [None, "final"]
    
    # 再次测试：初始化为 Continue (False)，start 覆盖为 Stop (True)
    scheduler2 = Scheduler(stop_on_error=False)
    scheduler2.add(task_fail)
    scheduler2.add(task_final)
    
    with pytest.raises(ValueError, match="Oops"):
        scheduler2.start(stop_on_error=True)

def test_scheduler_clear():
    """测试 clear 方法"""
    scheduler = Scheduler()
    scheduler.add(lambda: 1)
    scheduler.clear()
    results = scheduler.start()
    assert results == []

def test_scheduler_uninitialized_error():
    """测试未初始化时直接使用类 (应该被 main.py 的 wrapper 拦截)"""
    from ddtols import main
    original_state = main._INITIALIZED
    main._INITIALIZED = False
    
    try:
        with pytest.raises(RuntimeError, match="not initialized"):
            Scheduler()
    finally:
        main._INITIALIZED = original_state

def test_scheduler_custom_logger_name(caplog):
    """测试自定义 Logger 名称"""
    # 临时允许 ddtols 日志传播，以便 caplog 能捕获
    root_ddtols_logger = logging.getLogger("ddtols")
    original_propagate = root_ddtols_logger.propagate
    root_ddtols_logger.propagate = True
    
    try:
        custom_name = "my_custom_scheduler"
        scheduler = Scheduler(name=custom_name)
        
        # 我们期望日志名称是 ddtols.my_custom_scheduler (因为 get_logger 自动加前缀)
        expected_logger_name = f"ddtols.{custom_name}"
        
        # 验证 logger 属性
        assert scheduler.logger.name == expected_logger_name
        
        # 验证日志输出
        with caplog.at_level(logging.DEBUG, logger=expected_logger_name):
            scheduler.add(lambda: 1)
            scheduler.start()
            
        # 检查日志记录中是否包含预期的 logger 名称
        assert len(caplog.records) > 0
        for record in caplog.records:
            assert record.name == expected_logger_name
    finally:
        # 恢复 propagate 设置
        root_ddtols_logger.propagate = original_propagate
