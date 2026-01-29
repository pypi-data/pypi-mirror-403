import time
import pytest
import ddtols
from ddtols import Scheduler, SchedulerStatus

@pytest.fixture(autouse=True)
def init_ddtols():
    ddtols.init()

def demo_scheduler_progress():
    """演示 Scheduler 的进度监控和状态管理"""
    print("\n=== Scheduler 进度监控演示 ===")
    
    # 1. 定义信号回调函数
    def on_scheduler_event(event_type: str, data: dict):
        if event_type == "start":
            print(f"[事件] 调度器启动，总任务数: {data['total_tasks']}")
            
        elif event_type == "task_start":
            # 制作一个简单的进度条
            idx = data['index'] + 1
            total = data['total']
            percent = (idx / total) * 100
            bar_len = 20
            filled = int(percent / 100 * bar_len)
            bar = "█" * filled + "-" * (bar_len - filled)
            print(f"[事件] 任务开始: {data['task_name']} ({idx}/{total}) [{bar}] {percent:.1f}%")
            
        elif event_type == "task_success":
            print(f"       -> 任务完成，结果: {data['result']}")
            
        elif event_type == "task_error":
            print(f"       -> 任务出错: {data['error']}")
            
        elif event_type == "finish":
            print(f"[事件] 调度结束，最终状态: {data['status']}")

    # 2. 初始化调度器
    scheduler = Scheduler(name="progress_demo", signal_handler=on_scheduler_event)

    # 3. 添加一些模拟耗时任务
    def slow_task(name, duration):
        time.sleep(duration)
        return f"{name} done"
    
    # 模拟出错任务
    def error_task():
        raise ValueError("Simulated error")

    scheduler.add(slow_task, "Job A", 0.5)
    scheduler.add(slow_task, "Job B", 0.3)
    # scheduler.add(error_task, name="Error Job") # 可以取消注释测试错误处理
    scheduler.add(slow_task, "Job C", 0.2)
    
    print(f"[主线程] 启动前状态: {scheduler.status}")
    
    # 4. 启动调度器
    results = scheduler.start()
    
    print(f"[主线程] 结束后状态: {scheduler.status}")
    print(f"[主线程] 最终停留索引: {scheduler.current_index}")
    return results

def test_progress_monitoring():
    """测试用例：验证信号回调和状态更新"""
    events = []
    
    def handler(event, data):
        events.append((event, data))
        
    s = Scheduler(signal_handler=handler)
    
    def task1(): return 1
    def task2(): return 2
    
    s.add(task1)
    s.add(task2)
    
    assert s.status == SchedulerStatus.IDLE
    s.start()
    assert s.status == SchedulerStatus.COMPLETED
    
    # 验证事件序列
    event_types = [e[0] for e in events]
    expected_sequence = [
        "start", 
        "task_start", "task_success", # task1
        "task_start", "task_success", # task2
        "finish"
    ]
    assert event_types == expected_sequence
    
    # 验证数据
    start_event = next(e for e in events if e[0] == "start")
    assert start_event[1]['total_tasks'] == 2
    
    finish_event = next(e for e in events if e[0] == "finish")
    assert finish_event[1]['status'] == SchedulerStatus.COMPLETED

if __name__ == "__main__":
    # 如果直接运行此脚本，则执行演示函数
    ddtols.init()
    demo_scheduler_progress()
