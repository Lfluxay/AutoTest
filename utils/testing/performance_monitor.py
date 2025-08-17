import time
import psutil
import threading
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from utils.logging.logger import logger


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    thread_count: int = 0
    process_count: int = 0
    open_files: int = 0


@dataclass
class OperationMetrics:
    """操作性能指标"""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PerformanceMonitor:
    """增强的性能监控器"""

    def __init__(self, interval: float = 1.0):
        """
        初始化性能监控器

        Args:
            interval: 监控间隔（秒）
        """
        self.interval = interval
        self.monitoring = False
        self.metrics_history: List[PerformanceMetrics] = []
        self.operation_metrics: List[OperationMetrics] = []
        self.monitor_thread: Optional[threading.Thread] = None
        self.start_time: Optional[float] = None
        self._lock = threading.Lock()
        self._operation_stack: List[Dict[str, Any]] = []

        # 初始化基准值
        self._init_baseline()
    
    def _init_baseline(self):
        """初始化基准值"""
        try:
            # 获取初始网络和磁盘IO统计
            self.initial_net_io = psutil.net_io_counters()
            self.initial_disk_io = psutil.disk_io_counters()
        except Exception as e:
            logger.warning(f"初始化性能监控基准值失败: {e}")
            self.initial_net_io = None
            self.initial_disk_io = None
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            logger.warning("性能监控已在运行")
            return
        
        self.monitoring = True
        self.start_time = time.time()
        self.metrics_history.clear()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.monitoring:
            logger.warning("性能监控未在运行")
            return
        
        self.monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        
        logger.info("性能监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                if metrics:
                    self.metrics_history.append(metrics)
                
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"性能监控异常: {e}")
                time.sleep(self.interval)
    
    def _collect_metrics(self) -> Optional[PerformanceMetrics]:
        """收集性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent()
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            
            # 磁盘IO
            disk_io_read_mb = 0
            disk_io_write_mb = 0
            if self.initial_disk_io:
                try:
                    current_disk_io = psutil.disk_io_counters()
                    if current_disk_io:
                        disk_io_read_mb = (current_disk_io.read_bytes - self.initial_disk_io.read_bytes) / (1024 * 1024)
                        disk_io_write_mb = (current_disk_io.write_bytes - self.initial_disk_io.write_bytes) / (1024 * 1024)
                except Exception:
                    pass
            
            # 网络IO
            network_sent_mb = 0
            network_recv_mb = 0
            if self.initial_net_io:
                try:
                    current_net_io = psutil.net_io_counters()
                    if current_net_io:
                        network_sent_mb = (current_net_io.bytes_sent - self.initial_net_io.bytes_sent) / (1024 * 1024)
                        network_recv_mb = (current_net_io.bytes_recv - self.initial_net_io.bytes_recv) / (1024 * 1024)
                except Exception:
                    pass
            
            # 获取线程和进程信息
            try:
                current_process = psutil.Process()
                thread_count = current_process.num_threads()
                process_count = len(current_process.children(recursive=True)) + 1
                open_files = len(current_process.open_files())
            except Exception:
                thread_count = 0
                process_count = 0
                open_files = 0

            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                disk_io_read_mb=disk_io_read_mb,
                disk_io_write_mb=disk_io_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                thread_count=thread_count,
                process_count=process_count,
                open_files=open_files
            )
            
        except Exception as e:
            logger.error(f"收集性能指标失败: {e}")
            return None

    def start_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        开始监控操作

        Args:
            operation_name: 操作名称
            metadata: 元数据

        Returns:
            操作ID
        """
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        operation_data = {
            "operation_id": operation_id,
            "operation_name": operation_name,
            "start_time": time.time(),
            "metadata": metadata or {}
        }

        with self._lock:
            self._operation_stack.append(operation_data)

        logger.debug(f"开始监控操作: {operation_name} (ID: {operation_id})")
        return operation_id

    def end_operation(self, operation_id: str, success: bool = True,
                     error_message: Optional[str] = None) -> Optional[OperationMetrics]:
        """
        结束操作监控

        Args:
            operation_id: 操作ID
            success: 是否成功
            error_message: 错误消息

        Returns:
            操作性能指标
        """
        end_time = time.time()

        with self._lock:
            # 查找对应的操作
            operation_data = None
            for i, op in enumerate(self._operation_stack):
                if op["operation_id"] == operation_id:
                    operation_data = self._operation_stack.pop(i)
                    break

            if not operation_data:
                logger.warning(f"未找到操作: {operation_id}")
                return None

            # 创建操作指标
            metrics = OperationMetrics(
                operation_name=operation_data["operation_name"],
                start_time=operation_data["start_time"],
                end_time=end_time,
                duration=end_time - operation_data["start_time"],
                success=success,
                error_message=error_message,
                metadata=operation_data["metadata"]
            )

            self.operation_metrics.append(metrics)

            logger.debug(f"操作完成: {metrics.operation_name}, 耗时: {metrics.duration:.3f}s, "
                        f"成功: {success}")

            return metrics

    @contextmanager
    def monitor_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        操作监控上下文管理器

        Args:
            operation_name: 操作名称
            metadata: 元数据
        """
        operation_id = self.start_operation(operation_name, metadata)
        success = True
        error_message = None

        try:
            yield operation_id
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            self.end_operation(operation_id, success, error_message)
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前性能指标"""
        return self._collect_metrics()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取性能指标摘要"""
        if not self.metrics_history:
            return {}
        
        try:
            # 计算各项指标的统计信息
            cpu_values = [m.cpu_percent for m in self.metrics_history]
            memory_values = [m.memory_percent for m in self.metrics_history]
            memory_used_values = [m.memory_used_mb for m in self.metrics_history]
            
            summary = {
                'duration_seconds': time.time() - self.start_time if self.start_time else 0,
                'sample_count': len(self.metrics_history),
                'cpu': {
                    'avg': sum(cpu_values) / len(cpu_values),
                    'max': max(cpu_values),
                    'min': min(cpu_values)
                },
                'memory': {
                    'avg_percent': sum(memory_values) / len(memory_values),
                    'max_percent': max(memory_values),
                    'min_percent': min(memory_values),
                    'avg_used_mb': sum(memory_used_values) / len(memory_used_values),
                    'max_used_mb': max(memory_used_values),
                    'min_used_mb': min(memory_used_values)
                }
            }
            
            # 添加IO统计（如果有数据）
            if any(m.disk_io_read_mb > 0 or m.disk_io_write_mb > 0 for m in self.metrics_history):
                disk_read_values = [m.disk_io_read_mb for m in self.metrics_history]
                disk_write_values = [m.disk_io_write_mb for m in self.metrics_history]
                
                summary['disk_io'] = {
                    'total_read_mb': max(disk_read_values),
                    'total_write_mb': max(disk_write_values)
                }
            
            if any(m.network_sent_mb > 0 or m.network_recv_mb > 0 for m in self.metrics_history):
                net_sent_values = [m.network_sent_mb for m in self.metrics_history]
                net_recv_values = [m.network_recv_mb for m in self.metrics_history]
                
                summary['network_io'] = {
                    'total_sent_mb': max(net_sent_values),
                    'total_recv_mb': max(net_recv_values)
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"计算性能指标摘要失败: {e}")
            return {}
    
    def check_performance_thresholds(self, thresholds: Dict[str, float]) -> List[str]:
        """
        检查性能阈值
        
        Args:
            thresholds: 性能阈值配置
            
        Returns:
            超出阈值的警告列表
        """
        warnings = []
        
        if not self.metrics_history:
            return warnings
        
        try:
            summary = self.get_metrics_summary()
            
            # 检查CPU阈值
            cpu_threshold = thresholds.get('cpu_percent', 80.0)
            if summary.get('cpu', {}).get('max', 0) > cpu_threshold:
                warnings.append(f"CPU使用率超过阈值: {summary['cpu']['max']:.1f}% > {cpu_threshold}%")
            
            # 检查内存阈值
            memory_threshold = thresholds.get('memory_percent', 80.0)
            if summary.get('memory', {}).get('max_percent', 0) > memory_threshold:
                warnings.append(f"内存使用率超过阈值: {summary['memory']['max_percent']:.1f}% > {memory_threshold}%")
            
            # 检查磁盘IO阈值
            disk_io_threshold = thresholds.get('disk_io_mb', 100.0)
            disk_io = summary.get('disk_io', {})
            total_disk_io = disk_io.get('total_read_mb', 0) + disk_io.get('total_write_mb', 0)
            if total_disk_io > disk_io_threshold:
                warnings.append(f"磁盘IO超过阈值: {total_disk_io:.1f}MB > {disk_io_threshold}MB")
            
            # 检查网络IO阈值
            network_io_threshold = thresholds.get('network_io_mb', 50.0)
            network_io = summary.get('network_io', {})
            total_network_io = network_io.get('total_sent_mb', 0) + network_io.get('total_recv_mb', 0)
            if total_network_io > network_io_threshold:
                warnings.append(f"网络IO超过阈值: {total_network_io:.1f}MB > {network_io_threshold}MB")
            
        except Exception as e:
            logger.error(f"检查性能阈值失败: {e}")
            warnings.append(f"性能阈值检查异常: {e}")
        
        return warnings
    
    def export_metrics(self, file_path: str):
        """导出性能指标到文件"""
        try:
            import json
            
            data = {
                'summary': self.get_metrics_summary(),
                'metrics': [
                    {
                        'timestamp': m.timestamp,
                        'cpu_percent': m.cpu_percent,
                        'memory_percent': m.memory_percent,
                        'memory_used_mb': m.memory_used_mb,
                        'disk_io_read_mb': m.disk_io_read_mb,
                        'disk_io_write_mb': m.disk_io_write_mb,
                        'network_sent_mb': m.network_sent_mb,
                        'network_recv_mb': m.network_recv_mb
                    }
                    for m in self.metrics_history
                ]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"性能指标已导出到: {file_path}")
            
        except Exception as e:
            logger.error(f"导出性能指标失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_monitoring()


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()

# 便捷函数
def start_performance_monitoring(interval: float = 1.0):
    """开始性能监控"""
    global performance_monitor
    performance_monitor = PerformanceMonitor(interval)
    performance_monitor.start_monitoring()

def stop_performance_monitoring() -> Dict[str, Any]:
    """停止性能监控并返回摘要"""
    performance_monitor.stop_monitoring()
    return performance_monitor.get_metrics_summary()

def get_performance_summary() -> Dict[str, Any]:
    """获取性能摘要"""
    return performance_monitor.get_metrics_summary()
