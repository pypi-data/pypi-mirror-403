"""
测试装饰器模块
"""

import asyncio
import contextvars
import threading
from unittest.mock import Mock

import pytest

from ai4love_tools.tenant.context import clear_context, get_tenant_id, get_user_id, set_tenant_id
from ai4love_tools.tenant.decorators import extract_tenant_id, with_tenant_context
from ai4love_tools.tenant.exceptions import TenantIdMissingError, UserIdMissingError


class MockRequest:
    """模拟请求对象"""

    def __init__(self, headers: dict | None = None):
        self.headers = headers or {}


class TestExtractTenantId:
    """测试 @extract_tenant_id 装饰器"""

    def test_sync_function_with_request_param(self):
        """测试同步函数，通过参数名识别请求对象"""
        @extract_tenant_id
        def handler(request: MockRequest):
            return get_tenant_id()

        request = MockRequest({"X-Tenant-ID": "tenant_123", "X-User-ID": "user_456"})
        clear_context()
        result = handler(request)
        assert result == "tenant_123"
        assert get_user_id() == "user_456"

    def test_sync_function_with_req_param(self):
        """测试同步函数，通过 req 参数名识别请求对象"""
        @extract_tenant_id
        def handler(req: MockRequest):
            return get_tenant_id()

        request = MockRequest({"X-Tenant-ID": "tenant_123"})
        clear_context()
        result = handler(req=request)
        assert result == "tenant_123"

    def test_async_function_with_request_param(self):
        """测试异步函数，通过参数名识别请求对象"""
        @extract_tenant_id
        async def handler(request: MockRequest):
            return get_tenant_id()

        async def run_test():
            request = MockRequest({"X-Tenant-ID": "tenant_123", "X-User-ID": "user_456"})
            clear_context()
            result = await handler(request)
            assert result == "tenant_123"
            assert get_user_id() == "user_456"

        asyncio.run(run_test())

    def test_required_tenant_id_missing(self):
        """测试强制要求租户ID但缺失时抛出异常"""
        @extract_tenant_id(required_tenant_id=True)
        def handler(request: MockRequest):
            return get_tenant_id()

        request = MockRequest({})
        clear_context()
        with pytest.raises(TenantIdMissingError):
            handler(request)

    def test_required_user_id_missing(self):
        """测试强制要求用户ID但缺失时抛出异常"""
        @extract_tenant_id(required_user_id=True)
        def handler(request: MockRequest):
            return get_user_id()

        request = MockRequest({"X-Tenant-ID": "tenant_123"})
        clear_context()
        with pytest.raises(UserIdMissingError):
            handler(request)

    def test_custom_headers(self):
        """测试使用自定义请求头名称"""
        @extract_tenant_id(tenant_header="Custom-Tenant", user_header="Custom-User")
        def handler(request: MockRequest):
            return get_tenant_id(), get_user_id()

        request = MockRequest({"Custom-Tenant": "tenant_123", "Custom-User": "user_456"})
        clear_context()
        tenant_id, user_id = handler(request)
        assert tenant_id == "tenant_123"
        assert user_id == "user_456"

    def test_no_request_param(self):
        """测试没有请求对象参数时不会报错"""
        @extract_tenant_id
        def handler():
            return get_tenant_id()

        clear_context()
        result = handler()
        assert result is None

    def test_function_with_other_params(self):
        """测试函数有其他参数时正常工作"""
        @extract_tenant_id
        def handler(request: MockRequest, other_param: str):
            return get_tenant_id(), other_param

        request = MockRequest({"X-Tenant-ID": "tenant_123"})
        clear_context()
        tenant_id, other = handler(request, "test")
        assert tenant_id == "tenant_123"
        assert other == "test"

    def test_class_method(self):
        """测试装饰器应用于类方法"""
        class Handler:
            @extract_tenant_id
            def handle(self, request: MockRequest):
                return get_tenant_id()

        handler = Handler()
        request = MockRequest({"X-Tenant-ID": "tenant_123"})
        clear_context()
        result = handler.handle(request)
        assert result == "tenant_123"


class TestWithTenantContext:
    """测试 @with_tenant_context 装饰器"""

    def test_sync_function_preserves_context(self):
        """测试同步函数保留上下文"""
        @with_tenant_context
        def worker():
            return get_tenant_id()

        set_tenant_id("tenant_123")
        result = worker()
        assert result == "tenant_123"

    def test_async_function_preserves_context(self):
        """测试异步函数保留上下文"""
        @with_tenant_context
        async def async_worker():
            return get_tenant_id()

        async def run_test():
            set_tenant_id("tenant_123")
            result = await async_worker()
            assert result == "tenant_123"

        asyncio.run(run_test())

    def test_thread_context_preservation(self):
        """测试线程中上下文传递"""
        @with_tenant_context
        def worker():
            return get_tenant_id()

        set_tenant_id("tenant_123")
        result_container = []

        def thread_func():
            result_container.append(worker())

        thread = threading.Thread(target=thread_func)
        thread.start()
        thread.join()

        assert result_container[0] == "tenant_123"

    def test_require_tenant_with_context(self):
        """测试要求租户ID且存在时正常工作"""
        @with_tenant_context(require_tenant=True)
        def worker():
            return get_tenant_id()

        set_tenant_id("tenant_123")
        result = worker()
        assert result == "tenant_123"

    def test_require_tenant_without_context(self):
        """测试要求租户ID但不存在时抛出异常"""
        @with_tenant_context(require_tenant=True)
        def worker():
            return get_tenant_id()

        clear_context()
        with pytest.raises(TenantIdMissingError):
            worker()

    def test_function_with_params(self):
        """测试带参数的函数正常工作"""
        @with_tenant_context
        def worker(data: str):
            return get_tenant_id(), data

        set_tenant_id("tenant_123")
        tenant_id, data = worker("test")
        assert tenant_id == "tenant_123"
        assert data == "test"

    def test_function_with_return_value(self):
        """测试函数返回值正常传递"""
        @with_tenant_context
        def worker():
            return "result"

        set_tenant_id("tenant_123")
        result = worker()
        assert result == "result"

    def test_function_raises_exception(self):
        """测试函数异常正常传播"""
        @with_tenant_context
        def worker():
            raise ValueError("test error")

        set_tenant_id("tenant_123")
        with pytest.raises(ValueError, match="test error"):
            worker()
