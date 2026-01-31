"""
用户上下文管理模块
使用 threading.local() 和 contextvars.ContextVar 统一管理用户信息
兼容同步和异步场景
"""
import threading
from contextvars import ContextVar
from typing import Optional, Dict, Any


# 使用 threading.local() 存储同步上下文的用户信息（兼容多线程）
_local = threading.local()

# 使用 contextvars.ContextVar 存储异步上下文的用户信息（兼容异步任务）
_async_user_info: ContextVar[Optional[Dict[str, Any]]] = ContextVar('user_info', default=None)


def set_current_user(user_info: Dict[str, Any]):
    """
    设置当前上下文的用户信息（同时支持同步和异步）
    
    Args:
        user_info: 用户信息字典，包含以下字段：
            - user_id: 用户ID
            - username: 用户名
            - app_id: 应用ID
            - app_code: 应用代码
            - token: 访问令牌（可选）
            - roles: 角色列表（可选）
            - permissions: 权限列表（可选）
            - is_admin: 是否管理员（可选）
    """
    # 同时设置两个上下文，确保兼容性
    _local.user_info = user_info
    _async_user_info.set(user_info)


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    获取当前上下文的用户信息（同时支持同步和异步）
    
    Returns:
        用户信息字典，如果未设置则返回 None
    """
    # 优先从 async context 获取（异步场景）
    async_info = _async_user_info.get(None)
    if async_info is not None:
        return async_info
    
    # 从 threading.local 获取（同步场景）
    return getattr(_local, 'user_info', None)


def get_current_user_id() -> Optional[int]:
    """获取当前用户ID"""
    user_info = get_current_user()
    return user_info.get('user_id') if user_info else None


def get_current_username() -> Optional[str]:
    """获取当前用户名"""
    user_info = get_current_user()
    return user_info.get('username') if user_info else None


def get_current_app_id() -> Optional[int]:
    """获取当前应用ID"""
    user_info = get_current_user()
    return user_info.get('app_id') if user_info else None


def get_current_app_code() -> Optional[str]:
    """获取当前应用代码"""
    user_info = get_current_user()
    return user_info.get('app_code') if user_info else None


def is_current_user_admin() -> bool:
    """判断当前用户是否为管理员"""
    user_info = get_current_user()
    return user_info.get('is_admin', False) if user_info else False


def clear_current_user():
    """清理当前上下文的用户信息"""
    if hasattr(_local, 'user_info'):
        delattr(_local, 'user_info')
    # ContextVar 不需要手动清理，会自动管理


# ============ 请求上下文管理（可选的额外信息） ============

_async_request_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('request_context', default=None)


def set_request_context(**kwargs):
    """
    设置请求上下文信息
    
    可以存储以下信息：
        - ip_address: 客户端IP
        - user_agent: User Agent
        - request_id: 请求ID
        - trace_id: 追踪ID
    """
    # 同时设置两个上下文
    _local.request_context = kwargs
    _async_request_context.set(kwargs)


def get_request_context() -> Optional[Dict[str, Any]]:
    """获取请求上下文信息"""
    # 优先从 async context 获取
    async_ctx = _async_request_context.get(None)
    if async_ctx is not None:
        return async_ctx
    
    return getattr(_local, 'request_context', None)


def get_client_ip() -> Optional[str]:
    """获取客户端IP"""
    ctx = get_request_context()
    return ctx.get('ip_address') if ctx else None


def clear_request_context():
    """清理请求上下文"""
    if hasattr(_local, 'request_context'):
        delattr(_local, 'request_context')


# ============ 使用示例 ============
"""
使用示例：

1. 在 FastAPI 中间件中设置用户信息：
    
    from app.utils.user_context import set_current_user, clear_current_user
    
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        # 验证 token 并获取用户信息
        user_info = await verify_token_and_get_user(request)
        if user_info:
            set_current_user({
                'user_id': user_info.id,
                'username': user_info.username,
                'app_id': user_info.app_id,
                'app_code': user_info.app.code,
                'is_admin': user_info.is_admin
            })
        
        try:
            response = await call_next(request)
            return response
        finally:
            clear_current_user()


2. 在业务代码中使用：
    
    from app.utils.user_context import get_current_user_id, get_current_username
    
    async def some_business_logic():
        user_id = get_current_user_id()
        username = get_current_username()
        
        if user_id:
            logger.info(f"用户 {username}({user_id}) 执行了操作")


3. 在装饰器中使用：
    
    from functools import wraps
    from app.utils.user_context import is_current_user_admin
    
    def require_admin(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not is_current_user_admin():
                raise HTTPException(status_code=403, detail="需要管理员权限")
            return await func(*args, **kwargs)
        return wrapper
    
    @require_admin
    async def admin_only_endpoint():
        pass
"""
