"""
租户隔离装饰器

提供 @extract_tenant_id 和 @with_tenant_context 装饰器。
"""

import contextvars
import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

from ai4love_tools.tenant.context import get_tenant_id, set_tenant_id, set_user_id
from ai4love_tools.tenant.exceptions import TenantIdMissingError, UserIdMissingError
from ai4love_tools.tenant.extractor import (
    extract_tenant_id_from_request,
    extract_user_id_from_request,
)

F = TypeVar("F", bound=Callable[..., Any])


def _get_headers_debug_info(request: Any) -> tuple[list[str], list[str]]:
    """
    获取请求头的调试信息

    Returns:
        (available_headers, header_details) 元组
    """
    available_headers = []
    header_details = []
    if hasattr(request, "headers"):
        headers = request.headers
        try:
            # FastAPI 的 Headers 对象
            if hasattr(headers, "__iter__") and hasattr(headers, "items"):
                for key, value in headers.items():
                    header_details.append(f"{key}={value}")
                    available_headers.append(str(key))
            elif isinstance(headers, dict):
                available_headers = list(headers.keys())
                header_details = [f"{k}={v}" for k, v in headers.items()]
            elif hasattr(headers, "keys"):
                available_headers = list(headers.keys())
                # 尝试获取值
                for key in available_headers:
                    try:
                        value = headers.get(key) if hasattr(headers, "get") else "?"
                        header_details.append(f"{key}={value}")
                    except Exception:
                        header_details.append(f"{key}=?")
        except Exception:
            pass
    return available_headers, header_details


def extract_tenant_id(
    func: F | None = None,
    *,
    required_tenant_id: bool = False,
    required_user_id: bool = False,
    tenant_header: str = "X-Tenant-ID",
    user_header: str = "X-User-ID",
) -> Any:
    """
    装饰器：自动从请求头提取租户ID和用户ID并保存到上下文

    支持同步和异步函数，自动识别函数参数中的请求对象。

    Args:
        func: 被装饰的函数
        required_tenant_id: 是否强制要求请求头中有租户ID，默认 False
        required_user_id: 是否强制要求请求头中有用户ID，默认 False
        tenant_header: 租户ID请求头名称，默认 "X-Tenant-ID"
        user_header: 用户ID请求头名称，默认 "X-User-ID"

    Returns:
        装饰后的函数

    Example:
        @app.get("/users")
        @extract_tenant_id
        async def get_users(request: Request):
            tenant_id = get_tenant_id()
            return {"tenant_id": tenant_id}
    """
    if func is None:
        return functools.partial(
            extract_tenant_id,
            required_tenant_id=required_tenant_id,
            required_user_id=required_user_id,
            tenant_header=tenant_header,
            user_header=user_header,
        )

    sig = inspect.signature(func)
    is_async = inspect.iscoroutinefunction(func)

    # 识别请求对象参数
    request_param = None
    for param_name, param in sig.parameters.items():
        # 通过参数名识别（request, req等）
        if param_name.lower() in ("request", "req"):
            request_param = param_name
            break
        # 通过参数类型识别（Request类型）
        if param.annotation != inspect.Parameter.empty:
            try:
                # 尝试导入 FastAPI 的 Request
                from fastapi import Request as FastAPIRequest

                if param.annotation == FastAPIRequest or (
                    hasattr(param.annotation, "__origin__")
                    and FastAPIRequest in getattr(param.annotation, "__args__", [])
                ):
                    request_param = param_name
                    break
            except ImportError:
                pass

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        # 获取请求对象
        request = None
        if request_param:
            if request_param in kwargs:
                request = kwargs[request_param]
            elif request_param in sig.parameters:
                param_index = list(sig.parameters.keys()).index(request_param)
                if param_index < len(args):
                    request = args[param_index]

        # 提取租户ID和用户ID
        tenant_id = extract_tenant_id_from_request(request, tenant_header)
        user_id = extract_user_id_from_request(request, user_header)

        # 验证必需字段
        if required_tenant_id and not tenant_id:
            # 提供更详细的错误信息
            if request is None:
                raise TenantIdMissingError(
                    f"无法找到请求对象，请确保函数参数中包含 request 或 req 参数，"
                    f"或者参数类型为 Request。当前参数: {list(sig.parameters.keys())}"
                )
            # 尝试获取所有 headers 用于调试
            available_headers, header_details = _get_headers_debug_info(request)
            error_msg = (
                f"请求头中缺少必需的租户ID（{tenant_header}）。"
                f"可用请求头: {available_headers if available_headers else '无法获取'}"
            )
            if header_details:
                error_msg += f"\n请求头详情: {', '.join(header_details[:10])}"  # 最多显示10个
            raise TenantIdMissingError(error_msg)
        if required_user_id and not user_id:
            raise UserIdMissingError(f"请求头中缺少必需的用户ID（{user_header}）")

        # 保存到上下文
        set_tenant_id(tenant_id)
        set_user_id(user_id)

        # 调用原函数
        return func(*args, **kwargs)

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        # 获取请求对象
        request = None
        if request_param:
            if request_param in kwargs:
                request = kwargs[request_param]
            elif request_param in sig.parameters:
                param_index = list(sig.parameters.keys()).index(request_param)
                if param_index < len(args):
                    request = args[param_index]

        # 提取租户ID和用户ID
        tenant_id = extract_tenant_id_from_request(request, tenant_header)
        user_id = extract_user_id_from_request(request, user_header)

        # 验证必需字段
        if required_tenant_id and not tenant_id:
            # 提供更详细的错误信息
            if request is None:
                raise TenantIdMissingError(
                    f"无法找到请求对象，请确保函数参数中包含 request 或 req 参数，"
                    f"或者参数类型为 Request。当前参数: {list(sig.parameters.keys())}"
                )
            # 尝试获取所有 headers 用于调试
            available_headers, header_details = _get_headers_debug_info(request)
            error_msg = (
                f"请求头中缺少必需的租户ID（{tenant_header}）。"
                f"可用请求头: {available_headers if available_headers else '无法获取'}"
            )
            if header_details:
                error_msg += f"\n请求头详情: {', '.join(header_details[:10])}"  # 最多显示10个
            raise TenantIdMissingError(error_msg)
        if required_user_id and not user_id:
            raise UserIdMissingError(f"请求头中缺少必需的用户ID（{user_header}）")

        # 保存到上下文
        set_tenant_id(tenant_id)
        set_user_id(user_id)

        # 调用原函数
        return await func(*args, **kwargs)

    return async_wrapper if is_async else sync_wrapper


def with_tenant_context(func: F | None = None, *, require_tenant: bool = False) -> Any:
    """
    装饰器：自动复制租户上下文到新线程/任务

    用于多线程、后台任务等场景，确保在新线程中能够访问租户上下文。

    Args:
        func: 被装饰的函数
        require_tenant: 是否强制要求上下文中有租户ID，默认 False

    Returns:
        装饰后的函数

    Example:
        @with_tenant_context
        def background_task(data):
            tenant_id = get_tenant_id()
            process_data(data)
    """
    if func is None:
        return functools.partial(with_tenant_context, require_tenant=require_tenant)

    is_async = inspect.iscoroutinefunction(func)

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        # 复制当前上下文
        context = contextvars.copy_context()

        # 验证必需字段
        if require_tenant:
            current_tenant_id = get_tenant_id()
            if not current_tenant_id:
                raise TenantIdMissingError("上下文中缺少必需的租户ID")

        # 在新上下文中执行函数
        return context.run(func, *args, **kwargs)

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        # 在异步上下文中，contextvars 会自动传递，无需显式复制
        # 对于异步函数，contextvars 在同一个事件循环中会自动传递

        # 验证必需字段
        if require_tenant:
            current_tenant_id = get_tenant_id()
            if not current_tenant_id:
                raise TenantIdMissingError("上下文中缺少必需的租户ID")

        # 在异步上下文中，contextvars 会自动传递，但我们需要确保上下文已设置
        # 对于异步函数，contextvars 在同一个事件循环中会自动传递
        # 这里主要是为了兼容性和显式处理
        return await func(*args, **kwargs)

    return async_wrapper if is_async else sync_wrapper
