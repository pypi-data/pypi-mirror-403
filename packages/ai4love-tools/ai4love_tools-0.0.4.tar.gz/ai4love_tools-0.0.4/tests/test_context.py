"""
测试上下文存储管理模块
"""

import pytest

from ai4love_tools.tenant.context import (
    clear_context,
    clear_tenant_id,
    clear_user_id,
    get_tenant_id,
    get_user_id,
    set_tenant_id,
    set_user_id,
)


class TestContext:
    """测试上下文存储功能"""

    def test_get_tenant_id_default_none(self):
        """测试获取未设置的租户ID，应返回None"""
        clear_tenant_id()
        assert get_tenant_id() is None

    def test_get_user_id_default_none(self):
        """测试获取未设置的用户ID，应返回None"""
        clear_user_id()
        assert get_user_id() is None

    def test_set_and_get_tenant_id(self):
        """测试设置和获取租户ID"""
        set_tenant_id("tenant_123")
        assert get_tenant_id() == "tenant_123"

    def test_set_and_get_user_id(self):
        """测试设置和获取用户ID"""
        set_user_id("user_456")
        assert get_user_id() == "user_456"

    def test_set_tenant_id_none(self):
        """测试设置租户ID为None"""
        set_tenant_id("tenant_123")
        set_tenant_id(None)
        assert get_tenant_id() is None

    def test_set_user_id_none(self):
        """测试设置用户ID为None"""
        set_user_id("user_456")
        set_user_id(None)
        assert get_user_id() is None

    def test_clear_tenant_id(self):
        """测试清除租户ID"""
        set_tenant_id("tenant_123")
        clear_tenant_id()
        assert get_tenant_id() is None

    def test_clear_user_id(self):
        """测试清除用户ID"""
        set_user_id("user_456")
        clear_user_id()
        assert get_user_id() is None

    def test_clear_context(self):
        """测试清除所有上下文"""
        set_tenant_id("tenant_123")
        set_user_id("user_456")
        clear_context()
        assert get_tenant_id() is None
        assert get_user_id() is None

    def test_context_isolation(self):
        """测试上下文隔离（在不同上下文中设置不同的值）"""
        set_tenant_id("tenant_1")
        set_user_id("user_1")

        assert get_tenant_id() == "tenant_1"
        assert get_user_id() == "user_1"

        # 设置新值
        set_tenant_id("tenant_2")
        set_user_id("user_2")

        assert get_tenant_id() == "tenant_2"
        assert get_user_id() == "user_2"
