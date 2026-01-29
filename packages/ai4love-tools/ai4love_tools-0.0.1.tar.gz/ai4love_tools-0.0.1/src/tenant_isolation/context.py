"""
租户ID和用户ID的上下文存储管理

使用 contextvars.ContextVar 实现线程安全的上下文变量存储。
"""

import contextvars

# 创建上下文变量
_tenant_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "tenant_id", default=None
)
_user_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "user_id", default=None
)


def get_tenant_id() -> str | None:
    """
    获取当前上下文中的租户ID

    Returns:
        当前上下文中的租户ID，如果未设置则返回 None
    """
    return _tenant_id_var.get()


def get_user_id() -> str | None:
    """
    获取当前上下文中的用户ID

    Returns:
        当前上下文中的用户ID，如果未设置则返回 None
    """
    return _user_id_var.get()


def set_tenant_id(tenant_id: str | None) -> None:
    """
    设置租户ID到上下文

    Args:
        tenant_id: 租户ID，可以为 None
    """
    _tenant_id_var.set(tenant_id)


def set_user_id(user_id: str | None) -> None:
    """
    设置用户ID到上下文

    Args:
        user_id: 用户ID，可以为 None
    """
    _user_id_var.set(user_id)


def clear_tenant_id() -> None:
    """
    清除上下文中的租户ID
    """
    _tenant_id_var.set(None)


def clear_user_id() -> None:
    """
    清除上下文中的用户ID
    """
    _user_id_var.set(None)


def clear_context() -> None:
    """
    清除上下文中的租户ID和用户ID
    """
    clear_tenant_id()
    clear_user_id()
