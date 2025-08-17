"""
并行执行管理器
提供更强大的并行执行能力，包括智能负载均衡、资源管理等
"""
import os
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass
from queue import Queue, Empty
import psutil

from utils.logging.logger import logger
from utils.exceptions import AutoTestException
from utils.performance_monitor import PerformanceMonitor


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    success: bool
    result: Any
    error: Optional[str]
    duration: float
    worker_id: str


@dataclass
class WorkerStats:
    """工作进程统计信息"""
    worker_id: str
    tasks_completed: int
    total_duration: float
    success_count: int
    failure_count: int
    cpu_usage: float
    memory_usage: float


class ParallelExecutor:
    """并行执行管理器"""
    
    def __init__(self, max_workers: Optional[int] = None, execution_mode: str = "thread"):
        """
        初始化并行执行管理器
        
        Args:
            max_workers: 最大工作进程数，None表示自动检测
            execution_mode: 执行模式，'thread'或'process'
        """
        self.max_workers = max_workers or self._calculate_optimal_workers()
        self.execution_mode = execution_mode
        self.tasks_queue: Queue = Queue()
        self.results: List[TaskResult] = []
        self.worker_stats: Dict[str, WorkerStats] = {}
        self.performance_monitor = PerformanceMonitor()
        self._executor: Optional[Union[ThreadPoolExecutor, ProcessPoolExecutor]] = None
        self._running = False
        
        logger.info(f"并行执行管理器初始化完成: {self.execution_mode}模式, {self.max_workers}个工作进程")
    
    def _calculate_optimal_workers(self) -> int:
        """计算最优工作进程数"""
        cpu_count = multiprocessing.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # 基于CPU和内存计算最优工作进程数
        cpu_based = min(cpu_count * 2, 16)  # 不超过16个
        memory_based = max(int(memory_gb / 2), 1)  # 每2GB内存分配1个进程
        
        optimal = min(cpu_based, memory_based)
        logger.info(f"自动计算最优工作进程数: {optimal} (CPU: {cpu_count}, 内存: {memory_gb:.1f}GB)")
        
        return optimal
    
    def add_task(self, task_id: str, func: Callable, *args, **kwargs) -> None:
        """
        添加任务到执行队列
        
        Args:
            task_id: 任务ID
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
        """
        task = {
            'task_id': task_id,
            'func': func,
            'args': args,
            'kwargs': kwargs
        }
        self.tasks_queue.put(task)
        logger.debug(f"任务已添加到队列: {task_id}")
    
    def execute_all(self, timeout: Optional[float] = None) -> List[TaskResult]:
        """
        执行所有任务
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            任务执行结果列表
        """
        if self.tasks_queue.empty():
            logger.warning("任务队列为空")
            return []
        
        self._running = True
        self.results.clear()
        self.worker_stats.clear()
        
        # 启动性能监控
        self.performance_monitor.start_monitoring()
        
        try:
            # 创建执行器
            if self.execution_mode == "process":
                self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
            else:
                self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
            
            # 提交所有任务
            futures = []
            task_count = 0
            
            while not self.tasks_queue.empty():
                try:
                    task = self.tasks_queue.get_nowait()
                    future = self._executor.submit(self._execute_task, task)
                    futures.append((future, task['task_id']))
                    task_count += 1
                except Empty:
                    break
            
            logger.info(f"开始并行执行 {task_count} 个任务")
            
            # 等待任务完成
            completed_count = 0
            for future, task_id in as_completed(futures, timeout=timeout):
                try:
                    result = future.result()
                    self.results.append(result)
                    completed_count += 1
                    
                    if completed_count % 10 == 0 or completed_count == task_count:
                        logger.info(f"任务执行进度: {completed_count}/{task_count}")
                        
                except Exception as e:
                    error_result = TaskResult(
                        task_id=task_id,
                        success=False,
                        result=None,
                        error=str(e),
                        duration=0.0,
                        worker_id="unknown"
                    )
                    self.results.append(error_result)
                    logger.error(f"任务执行异常: {task_id}, 错误: {e}")
            
            return self.results
            
        except Exception as e:
            logger.error(f"并行执行异常: {e}")
            raise AutoTestException(f"并行执行失败: {str(e)}", "PARALLEL_EXECUTION_FAILED")
        
        finally:
            self._running = False
            self.performance_monitor.stop_monitoring()
            if self._executor:
                self._executor.shutdown(wait=True)
    
    def _execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """执行单个任务"""
        task_id = task['task_id']
        func = task['func']
        args = task['args']
        kwargs = task['kwargs']
        
        worker_id = f"{self.execution_mode}_{threading.current_thread().ident}"
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # 更新工作进程统计
            self._update_worker_stats(worker_id, True, duration)
            
            return TaskResult(
                task_id=task_id,
                success=True,
                result=result,
                error=None,
                duration=duration,
                worker_id=worker_id
            )
            
        except Exception as e:
            duration = time.time() - start_time
            
            # 更新工作进程统计
            self._update_worker_stats(worker_id, False, duration)
            
            return TaskResult(
                task_id=task_id,
                success=False,
                result=None,
                error=str(e),
                duration=duration,
                worker_id=worker_id
            )
    
    def _update_worker_stats(self, worker_id: str, success: bool, duration: float) -> None:
        """更新工作进程统计信息"""
        if worker_id not in self.worker_stats:
            self.worker_stats[worker_id] = WorkerStats(
                worker_id=worker_id,
                tasks_completed=0,
                total_duration=0.0,
                success_count=0,
                failure_count=0,
                cpu_usage=0.0,
                memory_usage=0.0
            )
        
        stats = self.worker_stats[worker_id]
        stats.tasks_completed += 1
        stats.total_duration += duration
        
        if success:
            stats.success_count += 1
        else:
            stats.failure_count += 1
        
        # 更新资源使用情况
        try:
            process = psutil.Process()
            stats.cpu_usage = process.cpu_percent()
            stats.memory_usage = process.memory_info().rss / (1024 * 1024)  # MB
        except Exception:
            pass
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        if not self.results:
            return {"message": "没有执行结果"}
        
        total_tasks = len(self.results)
        successful_tasks = sum(1 for r in self.results if r.success)
        failed_tasks = total_tasks - successful_tasks
        total_duration = sum(r.duration for r in self.results)
        avg_duration = total_duration / total_tasks if total_tasks > 0 else 0
        
        performance_summary = self.performance_monitor.get_metrics_summary()
        
        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "max_workers": self.max_workers,
            "execution_mode": self.execution_mode,
            "worker_stats": {k: v.__dict__ for k, v in self.worker_stats.items()},
            "performance_metrics": performance_summary
        }
    
    def stop(self) -> None:
        """停止执行"""
        self._running = False
        if self._executor:
            self._executor.shutdown(wait=False)
        logger.info("并行执行已停止")


# 便捷函数
def execute_parallel_tasks(
    tasks: List[Tuple[str, Callable, tuple, dict]], 
    max_workers: Optional[int] = None,
    execution_mode: str = "thread",
    timeout: Optional[float] = None
) -> List[TaskResult]:
    """
    并行执行任务的便捷函数
    
    Args:
        tasks: 任务列表，每个元素为(task_id, func, args, kwargs)
        max_workers: 最大工作进程数
        execution_mode: 执行模式
        timeout: 超时时间
        
    Returns:
        任务执行结果列表
    """
    executor = ParallelExecutor(max_workers, execution_mode)
    
    for task_id, func, args, kwargs in tasks:
        executor.add_task(task_id, func, *args, **kwargs)
    
    return executor.execute_all(timeout)
