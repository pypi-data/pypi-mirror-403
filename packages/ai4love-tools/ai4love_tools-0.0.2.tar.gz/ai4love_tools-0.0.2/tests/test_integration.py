"""
集成测试

测试多个模块协同工作的场景
"""

import asyncio
import threading
from unittest.mock import Mock

import pytest

from ai4love_tools.tenant.context import clear_context, get_tenant_id, get_user_id
from ai4love_tools.tenant.decorators import extract_tenant_id, with_tenant_context
from ai4love_tools.tenant.sql import tenant_execute


class MockRequest:
    """模拟请求对象"""

    def __init__(self, headers: dict | None = None):
        self.headers = headers or {}


class TestIntegration:
    """集成测试"""

    def setup_method(self):
        """每个测试前清理上下文"""
        clear_context()

    def test_extract_and_use_in_sql(self):
        """测试提取租户ID并在 SQL 中使用"""
        @extract_tenant_id
        def handler(request: MockRequest):
            def executor(sql: str, params: dict):
                return sql, params

            sql = "SELECT * FROM users WHERE status = :status"
            params = {"status": "active"}
            return tenant_execute(executor, sql, params)

        request = MockRequest({"X-Tenant-ID": "tenant_123"})
        result_sql, result_params = handler(request)

        assert "WHERE tenant_id = :tenant_id" in result_sql
        assert result_params["tenant_id"] == "tenant_123"
        assert result_params["status"] == "active"

    def test_extract_and_use_in_thread(self):
        """测试提取租户ID并在线程中使用"""
        @extract_tenant_id
        def handler(request: MockRequest):
            @with_tenant_context
            def worker():
                return get_tenant_id(), get_user_id()

            result_container = []

            def thread_func():
                result_container.append(worker())

            thread = threading.Thread(target=thread_func)
            thread.start()
            thread.join()

            return result_container[0]

        request = MockRequest({"X-Tenant-ID": "tenant_123", "X-User-ID": "user_456"})
        tenant_id, user_id = handler(request)

        assert tenant_id == "tenant_123"
        assert user_id == "user_456"

    def test_async_extract_and_use(self):
        """测试异步函数中提取和使用租户ID"""
        @extract_tenant_id
        async def async_handler(request: MockRequest):
            tenant_id = get_tenant_id()
            user_id = get_user_id()

            def executor(sql: str, params: dict):
                return sql, params

            sql = "SELECT * FROM users"
            result_sql, result_params = tenant_execute(executor, sql)

            return tenant_id, user_id, result_sql

        async def run_test():
            request = MockRequest({"X-Tenant-ID": "tenant_123", "X-User-ID": "user_456"})
            tenant_id, user_id, sql = await async_handler(request)

            assert tenant_id == "tenant_123"
            assert user_id == "user_456"
            assert "WHERE tenant_id = :tenant_id" in sql

        asyncio.run(run_test())

    def test_multiple_requests_isolation(self):
        """测试多个请求之间的上下文隔离"""
        @extract_tenant_id
        def handler(request: MockRequest):
            return get_tenant_id(), get_user_id()

        # 第一个请求
        request1 = MockRequest({"X-Tenant-ID": "tenant_1", "X-User-ID": "user_1"})
        tenant_id_1, user_id_1 = handler(request1)
        assert tenant_id_1 == "tenant_1"
        assert user_id_1 == "user_1"

        # 第二个请求
        request2 = MockRequest({"X-Tenant-ID": "tenant_2", "X-User-ID": "user_2"})
        tenant_id_2, user_id_2 = handler(request2)
        assert tenant_id_2 == "tenant_2"
        assert user_id_2 == "user_2"

        # 验证上下文已更新
        assert get_tenant_id() == "tenant_2"
        assert get_user_id() == "user_2"

    def test_nested_decorators(self):
        """测试嵌套装饰器"""
        @with_tenant_context
        @extract_tenant_id
        def handler(request: MockRequest):
            return get_tenant_id()

        request = MockRequest({"X-Tenant-ID": "tenant_123"})
        result = handler(request)
        assert result == "tenant_123"

    def test_context_preserved_through_multiple_calls(self):
        """测试上下文在多次调用中保持"""
        @extract_tenant_id
        def handler(request: MockRequest):
            return get_tenant_id()

        request = MockRequest({"X-Tenant-ID": "tenant_123"})
        result1 = handler(request)
        result2 = handler(request)

        assert result1 == "tenant_123"
        assert result2 == "tenant_123"

    def test_sql_without_tenant_in_context(self):
        """测试上下文中没有租户ID时 SQL 执行原样"""
        def executor(sql: str, params: dict):
            return sql, params

        sql = "SELECT * FROM users"
        params = {"status": "active"}
        result_sql, result_params = tenant_execute(executor, sql, params)

        assert result_sql == sql
        assert result_params == params

    def test_complex_workflow(self):
        """测试复杂工作流程"""
        @extract_tenant_id
        def api_handler(request: MockRequest):
            tenant_id = get_tenant_id()
            user_id = get_user_id()

            @with_tenant_context
            def background_task():
                return get_tenant_id(), get_user_id()

            def sql_executor(sql: str, params: dict):
                return sql, params

            sql = "SELECT * FROM users WHERE status = :status"
            params = {"status": "active"}
            sql_result = tenant_execute(sql_executor, sql, params)

            thread_result = []
            thread = threading.Thread(
                target=lambda: thread_result.append(background_task())
            )
            thread.start()
            thread.join()

            return {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "sql": sql_result[0],
                "thread_tenant_id": thread_result[0][0] if thread_result else None,
            }

        request = MockRequest({"X-Tenant-ID": "tenant_123", "X-User-ID": "user_456"})
        result = api_handler(request)

        assert result["tenant_id"] == "tenant_123"
        assert result["user_id"] == "user_456"
        assert "WHERE tenant_id = :tenant_id" in result["sql"]
        assert result["thread_tenant_id"] == "tenant_123"
