"""
SDK 客户端接口监控模块
提供异步队列提交接口统计数据到服务端
"""
import time
import queue
import threading
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime


class ApiStatsCollector:
    """接口统计收集器（异步队列方式）"""
    
    def __init__(
        self,
        api_url: str,
        app_id: str,
        app_secret: str,
        token: str,
        batch_size: int = 10,
        flush_interval: float = 5.0,
        enabled: bool = True
    ):
        """
        初始化统计收集器
        
        Args:
            api_url: 统计接口 URL（如：http://auth.example.com/api/sdk/stats/report/batch）
            app_id: 应用 ID
            app_secret: 应用密钥
            token: 用户访问令牌
            batch_size: 批量提交大小
            flush_interval: 刷新间隔（秒）
            enabled: 是否启用
        """
        self.api_url = api_url.rstrip('/')
        self.app_id = app_id
        self.app_secret = app_secret
        self.token = token
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.enabled = enabled
        
        self.queue = queue.Queue()
        self.running = True
        self.worker_thread = None
        
        if self.enabled:
            self.start()
    
    def start(self):
        """启动工作线程"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
    
    def stop(self):
        """停止工作线程"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=10)
    
    def collect(
        self,
        api_path: str,
        api_method: str,
        status_code: int,
        response_time: float,
        error_message: Optional[str] = None,
        request_params: Optional[Dict[str, Any]] = None
    ):
        """
        收集接口统计数据
        
        Args:
            api_path: 接口路径
            api_method: 请求方法
            status_code: 状态码
            response_time: 响应时间（秒）
            error_message: 错误信息
            request_params: 请求参数（包含 headers, query_params, view_params, request_body, form_params）
        """
        if not self.enabled:
            return
        
        try:
            stat_data = {
                'api_path': api_path,
                'api_method': api_method,
                'status_code': status_code,
                'response_time': response_time,
                'error_message': error_message,
                'request_params': request_params,
                'timestamp': datetime.utcnow().isoformat()
            }
            self.queue.put_nowait(stat_data)
        except queue.Full:
            pass  # 队列满了，丢弃数据
        except Exception:
            pass  # 静默失败，不影响主流程
    
    def _worker(self):
        """后台工作线程：批量提交统计数据"""
        buffer = []
        last_flush_time = time.time()
        
        while self.running:
            try:
                # 尝试从队列获取数据
                try:
                    stat_data = self.queue.get(timeout=1.0)
                    buffer.append(stat_data)
                except queue.Empty:
                    pass
                
                current_time = time.time()
                should_flush = (
                    len(buffer) >= self.batch_size or
                    (buffer and (current_time - last_flush_time) >= self.flush_interval)
                )
                
                if should_flush:
                    self._flush_buffer(buffer)
                    buffer = []
                    last_flush_time = current_time
                    
            except Exception:
                pass  # 静默失败
        
        # 停止前刷新剩余数据
        if buffer:
            self._flush_buffer(buffer)
    
    def _flush_buffer(self, buffer: List[Dict[str, Any]]):
        """刷新缓冲区：批量提交统计数据"""
        if not buffer:
            return
        
        try:
            headers = {
                'X-App-Id': self.app_id,
                'X-App-Secret': self.app_secret,
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            payload = {'stats': buffer}
            
            response = requests.post(
                f'{self.api_url}/stats/report/batch',
                json=payload,
                headers=headers,
                timeout=5
            )
            
            # 静默失败，不抛出异常
            if response.status_code != 200:
                pass
                
        except Exception:
            pass  # 静默失败，不影响主流程


# ============ 全局实例 ============

_global_collector: Optional[ApiStatsCollector] = None


def init_api_stats_collector(
    api_url: str,
    app_id: str,
    app_secret: str,
    token: str,
    batch_size: int = 10,
    flush_interval: float = 5.0,
    enabled: bool = True
) -> ApiStatsCollector:
    """
    初始化全局统计收集器
    
    Args:
        api_url: 统计接口 URL
        app_id: 应用 ID
        app_secret: 应用密钥
        token: 用户访问令牌
        batch_size: 批量提交大小
        flush_interval: 刷新间隔（秒）
        enabled: 是否启用
    
    Returns:
        统计收集器实例
    """
    global _global_collector
    _global_collector = ApiStatsCollector(
        api_url=api_url,
        app_id=app_id,
        app_secret=app_secret,
        token=token,
        batch_size=batch_size,
        flush_interval=flush_interval,
        enabled=enabled
    )
    return _global_collector


def get_api_stats_collector() -> Optional[ApiStatsCollector]:
    """获取全局统计收集器实例"""
    return _global_collector


def stop_api_stats_collector():
    """停止全局统计收集器"""
    global _global_collector
    if _global_collector:
        _global_collector.stop()
        _global_collector = None


def collect_api_stat(
    api_path: str,
    api_method: str,
    status_code: int,
    response_time: float,
    error_message: Optional[str] = None,
    request_params: Optional[Dict[str, Any]] = None
):
    """
    快捷方法：收集接口统计数据
    
    使用全局收集器实例
    """
    collector = get_api_stats_collector()
    if collector:
        collector.collect(
            api_path=api_path,
            api_method=api_method,
            status_code=status_code,
            response_time=response_time,
            error_message=error_message,
            request_params=request_params
        )


# ============ 使用示例 ============
"""
使用示例：

1. 应用启动时初始化：
    
    from huace_aigc_auth_client.api_stats_collector import init_api_stats_collector
    
    # 在应用启动时初始化
    init_api_stats_collector(
        api_url='http://auth.example.com/api/sdk',
        app_secret='your-app-secret',
        token='user-access-token',
        batch_size=10,
        flush_interval=5.0,
        enabled=True
    )


2. 在拦截器中使用：
    
    from huace_aigc_auth_client.api_stats_collector import collect_api_stat
    import time
    
    @app.middleware("http")
    async def monitor_middleware(request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            response_time = time.time() - start_time
            
            # 收集统计
            collect_api_stat(
                api_path=request.url.path,
                api_method=request.method,
                status_code=response.status_code,
                response_time=response_time
            )
            
            return response
        except Exception as e:
            response_time = time.time() - start_time
            collect_api_stat(
                api_path=request.url.path,
                api_method=request.method,
                status_code=500,
                response_time=response_time,
                error_message=str(e)
            )
            raise


3. 应用关闭时停止：
    
    from huace_aigc_auth_client.api_stats_collector import stop_api_stats_collector
    
    @app.on_event("shutdown")
    async def shutdown_event():
        stop_api_stats_collector()
"""
