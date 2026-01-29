import threading
import time
import pytest
import ddtols
from ddtols import Scheduler, SchedulerStatus

@pytest.fixture(autouse=True)
def init_ddtols():
    ddtols.init()

def demo_scheduler_stop():
    """演示通过外部线程停止 Scheduler"""
    print("\n=== Scheduler 外部停止演示 ===")
    
    # 1. 定义信号回调
    def on_scheduler_event(event_type: str, data: dict):
        if event_type == "start":
            print(f"[事件] 调度器启动，总任务数: {data['total_tasks']}")
        elif event_type == "task_start":
            print(f"[事件] 任务开始: {data['task_name']}")
        elif event_type == "task_success":
            print(f"       -> 任务完成")
        elif event_type == "finish":
            print(f"[事件] 调度结束，最终状态: {data['status']}")

    # 2. 初始化调度器
    scheduler = Scheduler(name="stop_demo", signal_handler=on_scheduler_event)

    # 3. 添加耗时任务
    def long_task(name):
        print(f"    (正在执行 {name}...)")
        time.sleep(1.0) # 模拟耗时
        return f"{name} done"

    scheduler.add(long_task, "Job 1")
    scheduler.add(long_task, "Job 2")
    scheduler.add(long_task, "Job 3 (Should be skipped)")
    scheduler.add(long_task, "Job 4 (Should be skipped)")
    
    # 4. 创建一个线程在 1.5 秒后（Job 2 执行中或刚结束时）发送停止信号
    def stopper():
        time.sleep(1.5)
        print("\n[外部信号] 发送停止指令...")
        scheduler.stop()

    stop_thread = threading.Thread(target=stopper)
    stop_thread.start()
    
    # 5. 启动调度器 (主线程阻塞在此)
    print(f"[主线程] 启动调度器...")
    results = scheduler.start()
    
    stop_thread.join()
    
    print(f"\n[主线程] 检查结果:")
    print(f"最终状态: {scheduler.status}")
    print(f"执行结果列表: {results}")
    print(f"已执行任务数: {len(results)}")
    
    return results

def test_stop_mechanism():
    """测试用例：验证 stop() 方法有效性"""
    scheduler = Scheduler()
    
    def task():
        time.sleep(0.1)
        return "ok"
        
    scheduler.add(task)
    scheduler.add(task)
    scheduler.add(task)
    
    # 在单独线程中运行 scheduler
    def run_scheduler():
        scheduler.start()
        
    t = threading.Thread(target=run_scheduler)
    t.start()
    
    # 等待一会儿让它开始运行
    time.sleep(0.15)
    
    # 发送停止信号
    scheduler.stop()
    
    t.join()
    
    # 验证状态和结果
    # 应该执行了 1 或 2 个任务，肯定小于 3
    assert scheduler.status == SchedulerStatus.STOPPED
    assert scheduler.current_index < 2  # 索引从0开始，<2 意味着没执行完所有

if __name__ == "__main__":
    ddtols.init()
    demo_scheduler_stop()
