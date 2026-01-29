"""
租户隔离功能模块

提供完整的租户ID提取、上下文存储、数据隔离等能力。
"""

from ai4love_tools import __version__
from ai4love_tools.tenant.context import (
    get_tenant_id,
    get_user_id,
    set_tenant_id,
    set_user_id,
)
from ai4love_tools.tenant.decorators import extract_tenant_id, with_tenant_context
from ai4love_tools.tenant.exceptions import (
    SQLRewriteError,
    TenantIdMissingError,
    TenantIsolationError,
    UserIdMissingError,
)
from ai4love_tools.tenant.extractor import (
    extract_tenant_id_from_request,
    extract_user_id_from_request,
)
from ai4love_tools.tenant.sql import (
    build_tenant_params,
    build_tenant_sql,
    tenant_execute,
)
from ai4love_tools.tenant.sqlalchemy_integration import enable_sqlalchemy_tenant_isolation

__all__ = [
    # 上下文管理
    "get_tenant_id",
    "get_user_id",
    "set_tenant_id",
    "set_user_id",
    # 装饰器
    "extract_tenant_id",
    "with_tenant_context",
    # 提取器
    "extract_tenant_id_from_request",
    "extract_user_id_from_request",
    # SQL 封装
    "tenant_execute",
    "build_tenant_sql",
    "build_tenant_params",
    # SQLAlchemy 集成
    "enable_sqlalchemy_tenant_isolation",
    # 异常
    "TenantIsolationError",
    "TenantIdMissingError",
    "UserIdMissingError",
    "SQLRewriteError",
    # 版本
    "__version__",
]
