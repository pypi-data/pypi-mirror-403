"""
SQL 封装函数

提供自动为 SQL 语句附加租户条件的封装函数。
"""

import re
from collections.abc import Callable
from typing import Any

from ai4love_tools.tenant.context import get_tenant_id
from ai4love_tools.tenant.exceptions import SQLRewriteError, TenantIdMissingError


def build_tenant_sql(
    sql: str,
    *,
    tenant_column: str = "tenant_id",
    placeholder_style: str = "named",
) -> str:
    """
    构建包含租户条件的 SQL 语句

    根据 SQL 类型（SELECT/INSERT/UPDATE/DELETE）自动追加租户条件。

    Args:
        sql: 原始 SQL 语句
        tenant_column: 租户字段名，默认 "tenant_id"
        placeholder_style: 占位符风格，支持 "named"（:name）、"qmark"（?）、"numeric"（:1），默认 "named"

    Returns:
        重写后的 SQL 语句

    Raises:
        SQLRewriteError: 当 SQL 无法安全重写时
    """
    sql = sql.strip()
    if not sql:
        raise SQLRewriteError("SQL 语句为空")

    # 检测是否已包含租户条件
    tenant_pattern = rf"\b{re.escape(tenant_column)}\s*="
    if re.search(tenant_pattern, sql, re.IGNORECASE):
        return sql

    # 识别 SQL 类型
    sql_upper = sql.upper()
    sql_type = None
    for stmt_type in ["SELECT", "INSERT", "UPDATE", "DELETE"]:
        if sql_upper.startswith(stmt_type):
            sql_type = stmt_type
            break

    if not sql_type:
        return sql

    tenant_id = get_tenant_id()
    if not tenant_id:
        return sql

    # 根据占位符风格生成占位符
    if placeholder_style == "named":
        placeholder = f":{tenant_column}"
    elif placeholder_style == "qmark":
        placeholder = "?"
    elif placeholder_style == "numeric":
        placeholder = ":1"
    else:
        placeholder = f":{tenant_column}"

    # 处理 SELECT/UPDATE/DELETE
    if sql_type in ["SELECT", "UPDATE", "DELETE"]:
        # 查找 WHERE 关键字
        where_match = re.search(r"\bWHERE\b", sql_upper, re.IGNORECASE)
        if where_match:
            # 已有 WHERE，追加 AND 条件
            where_pos = where_match.end()
            tenant_condition = f" AND {tenant_column} = {placeholder}"
            return sql[:where_pos] + tenant_condition + sql[where_pos:]

        # 没有 WHERE，添加 WHERE 条件
        if sql_type == "UPDATE":
            set_match = re.search(r"\bSET\b", sql_upper, re.IGNORECASE)
            if set_match:
                set_pos = set_match.end()
                remaining = sql[set_pos:]
                where_condition = f" WHERE {tenant_column} = {placeholder}"
                return sql[:set_pos] + remaining + where_condition

        where_condition = f" WHERE {tenant_column} = {placeholder}"
        return sql + where_condition

    # 处理 INSERT
    if sql_type == "INSERT":
        # 检查是否已包含租户字段
        if re.search(rf"\b{re.escape(tenant_column)}\b", sql, re.IGNORECASE):
            return sql

        insert_match = re.match(
            r"INSERT\s+INTO\s+(\w+)\s*(?:\(([^)]+)\))?\s*VALUES",
            sql,
            re.IGNORECASE,
        )
        if not insert_match:
            return sql

        columns = insert_match.group(2)

        if columns:
            columns_clean = columns.strip()
            new_columns = f"{columns_clean}, {tenant_column}"
            sql = sql.replace(f"({columns_clean})", f"({new_columns})", 1)
        else:
            return sql

        values_match = re.search(r"VALUES\s*\(", sql, re.IGNORECASE)
        if values_match:
            values_pos = values_match.end()
            paren_count = 1
            i = values_pos
            while i < len(sql) and paren_count > 0:
                if sql[i] == "(":
                    paren_count += 1
                elif sql[i] == ")":
                    paren_count -= 1
                i += 1

            if paren_count == 0:
                insert_pos = i - 1
                sql = sql[:insert_pos] + f", {placeholder}" + sql[insert_pos:]

        return sql

    return sql


def build_tenant_params(
    params: Any,
    tenant_id: str | int,
    *,
    placeholder_style: str = "named",
    tenant_column: str = "tenant_id",
) -> Any:
    """
    构建包含租户ID的参数

    Args:
        params: 原始参数（字典、元组或列表）
        tenant_id: 租户ID
        placeholder_style: 占位符风格，支持 "named"（:name）、"qmark"（?）、"numeric"（:1），默认 "named"
        tenant_column: 租户字段名，默认 "tenant_id"

    Returns:
        包含租户ID的参数
    """
    if placeholder_style == "named":
        if isinstance(params, dict):
            params = params.copy()
            params[tenant_column] = tenant_id
            return params
        if isinstance(params, (list, tuple)):
            params = list(params)
            params.append(tenant_id)
            return tuple(params) if isinstance(params, tuple) else params
        return {tenant_column: tenant_id}

    if placeholder_style in ["qmark", "numeric"]:
        if isinstance(params, (list, tuple)):
            params = list(params)
            params.append(tenant_id)
            return tuple(params) if isinstance(params, tuple) else params
        if isinstance(params, dict):
            params = list(params.values())
            params.append(tenant_id)
            return params
        return [tenant_id]

    return params


def tenant_execute(
    executor: Callable[[str, Any], Any],
    sql: str,
    params: Any = None,
    *,
    require_tenant: bool = False,
    tenant_column: str = "tenant_id",
    placeholder_style: str = "named",
) -> Any:
    """
    执行包含租户条件的 SQL 语句

    自动从上下文获取租户ID，重写 SQL 并追加租户条件，然后调用执行器执行。

    Args:
        executor: SQL 执行器函数，接受 (sql, params) 参数
        sql: 原始 SQL 语句
        params: SQL 参数
        require_tenant: 是否强制要求上下文中有租户ID，默认 False
        tenant_column: 租户字段名，默认 "tenant_id"
        placeholder_style: 占位符风格，默认 "named"

    Returns:
        执行器的返回结果

    Raises:
        TenantIdMissingError: 当 require_tenant=True 且上下文中没有租户ID时
        SQLRewriteError: 当 SQL 无法安全重写时
    """
    tenant_id = get_tenant_id()

    if require_tenant and not tenant_id:
        raise TenantIdMissingError("执行 SQL 需要租户ID，但上下文中未设置")

    if not tenant_id:
        return executor(sql, params)

    rewritten_sql = build_tenant_sql(
        sql, tenant_column=tenant_column, placeholder_style=placeholder_style
    )

    if rewritten_sql != sql:
        rewritten_params = build_tenant_params(
            params,
            tenant_id,
            placeholder_style=placeholder_style,
            tenant_column=tenant_column,
        )
    else:
        rewritten_params = params

    return executor(rewritten_sql, rewritten_params)
