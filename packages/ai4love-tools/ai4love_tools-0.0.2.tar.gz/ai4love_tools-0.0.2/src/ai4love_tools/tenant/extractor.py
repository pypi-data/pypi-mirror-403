"""
租户ID和用户ID提取器

从HTTP请求头中提取租户ID和用户ID。
"""

try:
    from fastapi import Request
except ImportError:
    Request = None


def extract_tenant_id_from_request(
    request, tenant_header: str = "X-Tenant-ID"
) -> str | None:
    """
    从HTTP请求头中提取租户ID

    Args:
        request: 请求对象（FastAPI的Request或其他框架的请求对象）
        tenant_header: 租户ID请求头名称，默认为 "X-Tenant-ID"

    Returns:
        租户ID，如果请求头中不存在则返回 None
    """
    if request is None:
        return None

    # 支持 FastAPI 的 Request 对象
    if Request is not None and isinstance(request, Request):
        return request.headers.get(tenant_header)

    # 支持其他框架的请求对象（通过 headers 属性或 get_header 方法）
    if hasattr(request, "headers"):
        headers = request.headers
        if isinstance(headers, dict):
            return headers.get(tenant_header)
        if hasattr(headers, "get"):
            return headers.get(tenant_header)

    # 支持通过方法获取请求头
    if hasattr(request, "get_header"):
        return request.get_header(tenant_header)

    return None


def extract_user_id_from_request(
    request, user_header: str = "X-User-ID"
) -> str | None:
    """
    从HTTP请求头中提取用户ID

    Args:
        request: 请求对象（FastAPI的Request或其他框架的请求对象）
        user_header: 用户ID请求头名称，默认为 "X-User-ID"

    Returns:
        用户ID，如果请求头中不存在则返回 None
    """
    if request is None:
        return None

    # 支持 FastAPI 的 Request 对象
    if Request is not None and isinstance(request, Request):
        return request.headers.get(user_header)

    # 支持其他框架的请求对象（通过 headers 属性或 get_header 方法）
    if hasattr(request, "headers"):
        headers = request.headers
        if isinstance(headers, dict):
            return headers.get(user_header)
        if hasattr(headers, "get"):
            return headers.get(user_header)

    # 支持通过方法获取请求头
    if hasattr(request, "get_header"):
        return request.get_header(user_header)

    return None
