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
        # FastAPI 的 headers 是大小写不敏感的，直接使用 get 方法即可
        # 但为了兼容性，也尝试大小写变体
        value = request.headers.get(tenant_header)
        if value is None:
            # 尝试小写版本（FastAPI headers 应该是大小写不敏感的，但为了保险）
            value = request.headers.get(tenant_header.lower())
        if value is None:
            # 尝试其他常见格式
            value = request.headers.get(tenant_header.replace("-", "_"))
        # 如果还是 None，尝试直接遍历 headers（某些情况下可能需要）
        if value is None and hasattr(request.headers, "__iter__"):
            for key, val in request.headers.items():
                if key.lower() == tenant_header.lower():
                    value = val
                    break
        return value

    # 支持其他框架的请求对象（通过 headers 属性或 get_header 方法）
    if hasattr(request, "headers"):
        headers = request.headers
        if isinstance(headers, dict):
            # 字典类型，尝试多种键格式
            value = headers.get(tenant_header)
            if value is None:
                value = headers.get(tenant_header.lower())
            if value is None:
                value = headers.get(tenant_header.upper())
            return value
        if hasattr(headers, "get"):
            # 类似字典的对象（如 FastAPI Headers）
            value = headers.get(tenant_header)
            if value is None:
                value = headers.get(tenant_header.lower())
            return value

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
        # FastAPI 的 headers 是大小写不敏感的，直接使用 get 方法即可
        value = request.headers.get(user_header)
        if value is None:
            value = request.headers.get(user_header.lower())
        if value is None:
            value = request.headers.get(user_header.replace("-", "_"))
        return value

    # 支持其他框架的请求对象（通过 headers 属性或 get_header 方法）
    if hasattr(request, "headers"):
        headers = request.headers
        if isinstance(headers, dict):
            # 字典类型，尝试多种键格式
            value = headers.get(user_header)
            if value is None:
                value = headers.get(user_header.lower())
            if value is None:
                value = headers.get(user_header.upper())
            return value
        if hasattr(headers, "get"):
            # 类似字典的对象（如 FastAPI Headers）
            value = headers.get(user_header)
            if value is None:
                value = headers.get(user_header.lower())
            return value

    # 支持通过方法获取请求头
    if hasattr(request, "get_header"):
        return request.get_header(user_header)

    return None
