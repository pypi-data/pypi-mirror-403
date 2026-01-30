"""
测试租户ID和用户ID提取器模块
"""

import pytest

from ai4love_tools.tenant.extractor import (
    extract_tenant_id_from_request,
    extract_user_id_from_request,
)


class MockRequest:
    """模拟请求对象"""

    def __init__(self, headers: dict | None = None):
        self.headers = headers or {}


class MockRequestWithGetHeader:
    """模拟带 get_header 方法的请求对象"""

    def __init__(self, headers: dict | None = None):
        self._headers = headers or {}

    def get_header(self, name: str):
        """获取请求头"""
        return self._headers.get(name)


class TestExtractor:
    """测试提取器功能"""

    def test_extract_tenant_id_from_fastapi_request(self):
        """测试从 FastAPI Request 对象提取租户ID"""
        try:
            from fastapi import Request

            # 创建模拟的 FastAPI Request
            class FastAPIRequest:
                def __init__(self, headers: dict):
                    self.headers = headers

            request = FastAPIRequest({"X-Tenant-ID": "tenant_123"})
            result = extract_tenant_id_from_request(request)
            assert result == "tenant_123"
        except ImportError:
            pytest.skip("FastAPI 未安装")

    def test_extract_tenant_id_from_dict_headers(self):
        """测试从字典类型的 headers 提取租户ID"""
        request = MockRequest({"X-Tenant-ID": "tenant_123"})
        result = extract_tenant_id_from_request(request)
        assert result == "tenant_123"

    def test_extract_tenant_id_from_headers_with_get(self):
        """测试从带 get 方法的 headers 提取租户ID"""
        class Headers:
            def __init__(self, headers: dict):
                self._headers = headers

            def get(self, key: str):
                return self._headers.get(key)

        class Request:
            def __init__(self, headers: dict):
                self.headers = Headers(headers)

        request = Request({"X-Tenant-ID": "tenant_123"})
        result = extract_tenant_id_from_request(request)
        assert result == "tenant_123"

    def test_extract_tenant_id_from_get_header_method(self):
        """测试从 get_header 方法提取租户ID"""
        request = MockRequestWithGetHeader({"X-Tenant-ID": "tenant_123"})
        result = extract_tenant_id_from_request(request)
        assert result == "tenant_123"

    def test_extract_tenant_id_not_found(self):
        """测试提取不存在的租户ID"""
        request = MockRequest({})
        result = extract_tenant_id_from_request(request)
        assert result is None

    def test_extract_tenant_id_none_request(self):
        """测试传入 None 请求对象"""
        result = extract_tenant_id_from_request(None)
        assert result is None

    def test_extract_tenant_id_custom_header(self):
        """测试使用自定义请求头名称"""
        request = MockRequest({"Custom-Tenant-Header": "tenant_123"})
        result = extract_tenant_id_from_request(request, tenant_header="Custom-Tenant-Header")
        assert result == "tenant_123"

    def test_extract_user_id_from_fastapi_request(self):
        """测试从 FastAPI Request 对象提取用户ID"""
        try:
            from fastapi import Request

            class FastAPIRequest:
                def __init__(self, headers: dict):
                    self.headers = headers

            request = FastAPIRequest({"X-User-ID": "user_456"})
            result = extract_user_id_from_request(request)
            assert result == "user_456"
        except ImportError:
            pytest.skip("FastAPI 未安装")

    def test_extract_user_id_from_dict_headers(self):
        """测试从字典类型的 headers 提取用户ID"""
        request = MockRequest({"X-User-ID": "user_456"})
        result = extract_user_id_from_request(request)
        assert result == "user_456"

    def test_extract_user_id_not_found(self):
        """测试提取不存在的用户ID"""
        request = MockRequest({})
        result = extract_user_id_from_request(request)
        assert result is None

    def test_extract_user_id_none_request(self):
        """测试传入 None 请求对象"""
        result = extract_user_id_from_request(None)
        assert result is None

    def test_extract_user_id_custom_header(self):
        """测试使用自定义请求头名称"""
        request = MockRequest({"Custom-User-Header": "user_456"})
        result = extract_user_id_from_request(request, user_header="Custom-User-Header")
        assert result == "user_456"
