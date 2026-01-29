"""
测试 SQL 封装模块
"""

import pytest

from ai4love_tools.tenant.context import clear_context, get_tenant_id, set_tenant_id
from ai4love_tools.tenant.exceptions import SQLRewriteError, TenantIdMissingError
from ai4love_tools.tenant.sql import (
    build_tenant_params,
    build_tenant_sql,
    tenant_execute,
)


class TestBuildTenantSql:
    """测试 build_tenant_sql 函数"""

    def setup_method(self):
        """每个测试前清理上下文"""
        clear_context()

    def test_empty_sql_raises_error(self):
        """测试空 SQL 语句抛出异常"""
        with pytest.raises(SQLRewriteError):
            build_tenant_sql("")

    def test_sql_without_tenant_id_returns_original(self):
        """测试上下文中没有租户ID时返回原 SQL"""
        sql = "SELECT * FROM users"
        result = build_tenant_sql(sql)
        assert result == sql

    def test_select_without_where(self):
        """测试 SELECT 语句没有 WHERE 时追加 WHERE 条件"""
        set_tenant_id("tenant_123")
        sql = "SELECT * FROM users"
        result = build_tenant_sql(sql)
        assert "WHERE tenant_id = :tenant_id" in result

    def test_select_with_where(self):
        """测试 SELECT 语句已有 WHERE 时追加 AND 条件"""
        set_tenant_id("tenant_123")
        sql = "SELECT * FROM users WHERE status = 'active'"
        result = build_tenant_sql(sql)
        assert "AND tenant_id = :tenant_id" in result
        assert "WHERE status = 'active'" in result

    def test_update_without_where(self):
        """测试 UPDATE 语句没有 WHERE 时追加 WHERE 条件"""
        set_tenant_id("tenant_123")
        sql = "UPDATE users SET status = 'active'"
        result = build_tenant_sql(sql)
        assert "WHERE tenant_id = :tenant_id" in result

    def test_update_with_where(self):
        """测试 UPDATE 语句已有 WHERE 时追加 AND 条件"""
        set_tenant_id("tenant_123")
        sql = "UPDATE users SET status = 'active' WHERE id = 1"
        result = build_tenant_sql(sql)
        assert "AND tenant_id = :tenant_id" in result

    def test_delete_without_where(self):
        """测试 DELETE 语句没有 WHERE 时追加 WHERE 条件"""
        set_tenant_id("tenant_123")
        sql = "DELETE FROM users"
        result = build_tenant_sql(sql)
        assert "WHERE tenant_id = :tenant_id" in result

    def test_delete_with_where(self):
        """测试 DELETE 语句已有 WHERE 时追加 AND 条件"""
        set_tenant_id("tenant_123")
        sql = "DELETE FROM users WHERE id = 1"
        result = build_tenant_sql(sql)
        assert "AND tenant_id = :tenant_id" in result

    def test_insert_with_columns(self):
        """测试 INSERT 语句有列清单时追加租户列"""
        set_tenant_id("tenant_123")
        sql = "INSERT INTO users (name, email) VALUES (:name, :email)"
        result = build_tenant_sql(sql)
        assert "tenant_id" in result
        assert ":tenant_id" in result

    def test_insert_already_has_tenant_id(self):
        """测试 INSERT 语句已包含租户字段时不再追加"""
        set_tenant_id("tenant_123")
        sql = "INSERT INTO users (name, tenant_id) VALUES (:name, :tenant_id)"
        result = build_tenant_sql(sql)
        # 应该保持原样，不重复添加
        assert result.count("tenant_id") == 2  # 列名和占位符各一个

    def test_sql_already_has_tenant_condition(self):
        """测试 SQL 已包含租户条件时不再追加"""
        set_tenant_id("tenant_123")
        sql = "SELECT * FROM users WHERE tenant_id = :tenant_id"
        result = build_tenant_sql(sql)
        assert result == sql

    def test_custom_tenant_column(self):
        """测试使用自定义租户字段名"""
        set_tenant_id("tenant_123")
        sql = "SELECT * FROM users"
        result = build_tenant_sql(sql, tenant_column="custom_tenant_id")
        assert "custom_tenant_id = :custom_tenant_id" in result

    def test_qmark_placeholder_style(self):
        """测试使用 qmark 占位符风格"""
        set_tenant_id("tenant_123")
        sql = "SELECT * FROM users"
        result = build_tenant_sql(sql, placeholder_style="qmark")
        assert "tenant_id = ?" in result

    def test_numeric_placeholder_style(self):
        """测试使用 numeric 占位符风格"""
        set_tenant_id("tenant_123")
        sql = "SELECT * FROM users"
        result = build_tenant_sql(sql, placeholder_style="numeric")
        assert "tenant_id = :1" in result

    def test_unknown_sql_type_returns_original(self):
        """测试未知 SQL 类型时返回原 SQL"""
        set_tenant_id("tenant_123")
        sql = "CREATE TABLE users (id INT)"
        result = build_tenant_sql(sql)
        assert result == sql


class TestBuildTenantParams:
    """测试 build_tenant_params 函数"""

    def test_named_style_with_dict(self):
        """测试 named 风格，参数为字典"""
        params = {"name": "test", "email": "test@example.com"}
        result = build_tenant_params(params, "tenant_123", placeholder_style="named")
        assert result["tenant_id"] == "tenant_123"
        assert result["name"] == "test"
        assert result["email"] == "test@example.com"

    def test_named_style_with_list(self):
        """测试 named 风格，参数为列表"""
        params = ["test", "test@example.com"]
        result = build_tenant_params(params, "tenant_123", placeholder_style="named")
        assert isinstance(result, list)
        assert result[-1] == "tenant_123"

    def test_named_style_with_tuple(self):
        """测试 named 风格，参数为元组"""
        params = ("test", "test@example.com")
        result = build_tenant_params(params, "tenant_123", placeholder_style="named")
        assert isinstance(result, tuple)
        assert result[-1] == "tenant_123"

    def test_named_style_with_none(self):
        """测试 named 风格，参数为 None"""
        result = build_tenant_params(None, "tenant_123", placeholder_style="named")
        assert result == {"tenant_id": "tenant_123"}

    def test_qmark_style_with_list(self):
        """测试 qmark 风格，参数为列表"""
        params = ["test", "test@example.com"]
        result = build_tenant_params(params, "tenant_123", placeholder_style="qmark")
        assert isinstance(result, list)
        assert result[-1] == "tenant_123"

    def test_qmark_style_with_dict(self):
        """测试 qmark 风格，参数为字典"""
        params = {"name": "test", "email": "test@example.com"}
        result = build_tenant_params(params, "tenant_123", placeholder_style="qmark")
        assert isinstance(result, list)
        assert "tenant_123" in result

    def test_custom_tenant_column(self):
        """测试使用自定义租户字段名"""
        params = {}
        result = build_tenant_params(
            params, "tenant_123", placeholder_style="named", tenant_column="custom_tenant_id"
        )
        assert result["custom_tenant_id"] == "tenant_123"


class TestTenantExecute:
    """测试 tenant_execute 函数"""

    def setup_method(self):
        """每个测试前清理上下文"""
        clear_context()

    def test_execute_without_tenant_id(self):
        """测试上下文中没有租户ID时执行原 SQL"""
        def executor(sql: str, params: dict):
            return sql, params

        sql = "SELECT * FROM users"
        params = {}
        result_sql, result_params = tenant_execute(executor, sql, params)
        assert result_sql == sql
        assert result_params == params

    def test_execute_with_tenant_id(self):
        """测试上下文中存在租户ID时重写 SQL"""
        set_tenant_id("tenant_123")

        def executor(sql: str, params: dict):
            return sql, params

        sql = "SELECT * FROM users"
        params = {}
        result_sql, result_params = tenant_execute(executor, sql, params)
        assert "WHERE tenant_id = :tenant_id" in result_sql
        assert result_params["tenant_id"] == "tenant_123"

    def test_require_tenant_without_context(self):
        """测试要求租户ID但上下文中没有时抛出异常"""
        def executor(sql: str, params: dict):
            return sql, params

        sql = "SELECT * FROM users"
        with pytest.raises(TenantIdMissingError):
            tenant_execute(executor, sql, require_tenant=True)

    def test_require_tenant_with_context(self):
        """测试要求租户ID且存在时正常执行"""
        set_tenant_id("tenant_123")

        def executor(sql: str, params: dict):
            return sql, params

        sql = "SELECT * FROM users"
        result_sql, result_params = tenant_execute(executor, sql, require_tenant=True)
        assert "WHERE tenant_id = :tenant_id" in result_sql

    def test_executor_return_value_preserved(self):
        """测试执行器返回值正常传递"""
        set_tenant_id("tenant_123")

        def executor(sql: str, params: dict):
            return {"rows": [{"id": 1, "name": "test"}]}

        sql = "SELECT * FROM users"
        result = tenant_execute(executor, sql)
        assert "rows" in result
        assert len(result["rows"]) == 1

    def test_custom_tenant_column(self):
        """测试使用自定义租户字段名"""
        set_tenant_id("tenant_123")

        def executor(sql: str, params: dict):
            return sql, params

        sql = "SELECT * FROM users"
        result_sql, result_params = tenant_execute(
            executor, sql, tenant_column="custom_tenant_id"
        )
        assert "custom_tenant_id = :custom_tenant_id" in result_sql
        assert result_params["custom_tenant_id"] == "tenant_123"

    def test_custom_placeholder_style(self):
        """测试使用自定义占位符风格"""
        set_tenant_id("tenant_123")

        def executor(sql: str, params: list):
            return sql, params

        sql = "SELECT * FROM users"
        result_sql, result_params = tenant_execute(
            executor, sql, params=[], placeholder_style="qmark"
        )
        assert "tenant_id = ?" in result_sql
        assert isinstance(result_params, list)
        assert result_params[-1] == "tenant_123"
