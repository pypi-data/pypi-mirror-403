"""Example Celery tasks"""

from src.tasks import task


@task(name="example_task", bind=True, retry_backoff=True, retry_kwargs={"max_retries": 3})
def example_task(self, *args, **kwargs):
    """示例任务
    
    这是一个示例任务，演示了如何创建和使用 Celery 任务。
    
    Args:
        *args: 任意位置参数
        **kwargs: 任意关键字参数
    
    Returns:
        dict: 包含任务结果的字典
    """
    try:
        # 模拟任务执行时间
        import time
        time.sleep(2)
        
        # 计算结果
        result = sum(args) if args else 0
        
        return {
            "result": result,
            "args": args,
            "kwargs": kwargs,
            "message": "Task executed successfully!"
        }
    except Exception as e:
        # 记录错误日志
        self.logger.error(f"Error executing example_task: {str(e)}")
        # 任务失败，自动重试
        self.retry(exc=e)


@task(name="long_running_task", bind=True, retry_backoff=True, retry_kwargs={"max_retries": 2})
def long_running_task(self, iterations: int = 10):
    """长时间运行的示例任务
    
    这个任务模拟了一个长时间运行的任务，通过迭代次数控制运行时间。
    
    Args:
        iterations: 迭代次数，每次迭代休眠 1 秒
    
    Returns:
        dict: 包含任务执行结果的字典
    """
    try:
        # 模拟长时间运行的任务
        import time
        results = []
        
        for i in range(iterations):
            # 执行一些计算
            result = i * i
            results.append(result)
            
            # 休眠 1 秒
            time.sleep(1)
            
            # 更新任务进度（可选）
            self.update_state(state="PROGRESS", meta={"current": i + 1, "total": iterations})
        
        return {
            "results": results,
            "total_iterations": iterations,
            "message": "Long running task completed successfully!"
        }
    except Exception as e:
        self.logger.error(f"Error executing long_running_task: {str(e)}")
        self.retry(exc=e)
