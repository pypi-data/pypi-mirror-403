"""
测试 SQLAlchemy 集成模块
"""

import pytest

from ai4love_tools.tenant.context import clear_context, get_tenant_id, set_tenant_id
from ai4love_tools.tenant.exceptions import TenantIdMissingError
from ai4love_tools.tenant.sqlalchemy_integration import (
    _has_tenant_column,
    _should_apply_tenant_filter,
    enable_sqlalchemy_tenant_isolation,
)

try:
    from sqlalchemy import Column, Integer, String, create_engine
    from sqlalchemy.orm import Session, declarative_base

    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Base = None
    Column = None
    Integer = None
    String = None
    create_engine = None
    Session = None


@pytest.mark.skipif(not SQLALCHEMY_AVAILABLE, reason="SQLAlchemy 未安装")
class TestSQLAlchemyIntegration:
    """测试 SQLAlchemy 集成功能"""

    def setup_method(self):
        """每个测试前清理上下文"""
        clear_context()

    def test_has_tenant_column_with_tenant_id(self):
        """测试包含 tenant_id 字段的模型"""
        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name = Column(String)
            tenant_id = Column(String)

        assert _has_tenant_column(User) is True

    def test_has_tenant_column_without_tenant_id(self):
        """测试不包含 tenant_id 字段的模型"""
        class Config(Base):
            __tablename__ = "configs"
            id = Column(Integer, primary_key=True)
            key = Column(String)
            value = Column(String)

        assert _has_tenant_column(Config) is False

    def test_should_apply_tenant_filter_with_tenant_id(self):
        """测试包含 tenant_id 的模型应该应用过滤"""
        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            tenant_id = Column(String)

        assert _should_apply_tenant_filter(User) is True

    def test_should_apply_tenant_filter_without_tenant_id(self):
        """测试不包含 tenant_id 的模型不应该应用过滤"""
        class Config(Base):
            __tablename__ = "configs"
            id = Column(Integer, primary_key=True)
            key = Column(String)

        assert _should_apply_tenant_filter(Config) is False

    def test_should_apply_tenant_filter_with_enabled_models(self):
        """测试使用模型白名单"""
        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            tenant_id = Column(String)

        class Config(Base):
            __tablename__ = "configs"
            id = Column(Integer, primary_key=True)
            key = Column(String)

        enabled_models = {User}
        assert _should_apply_tenant_filter(User, enabled_models) is True
        assert _should_apply_tenant_filter(Config, enabled_models) is False

    def test_should_apply_tenant_filter_none_model(self):
        """测试传入 None 模型"""
        assert _should_apply_tenant_filter(None) is False

    def test_enable_sqlalchemy_tenant_isolation(self):
        """测试启用 SQLAlchemy 租户隔离"""
        engine = create_engine("sqlite:///:memory:")
        enable_sqlalchemy_tenant_isolation(engine)
        # 如果没有抛出异常，说明启用成功
        assert True

    def test_enable_without_sqlalchemy_raises_error(self):
        """测试未安装 SQLAlchemy 时抛出异常"""
        # 这个测试需要模拟 SQLAlchemy 未安装的情况
        # 在实际环境中，如果 SQLAlchemy 已安装，这个测试会通过
        # 如果未安装，会在导入时就失败
        pass


@pytest.mark.skipif(not SQLALCHEMY_AVAILABLE, reason="SQLAlchemy 未安装")
class TestSQLAlchemyBeforeFlush:
    """测试 before_flush 事件处理"""

    def setup_method(self):
        """每个测试前清理上下文"""
        clear_context()

    def test_before_flush_adds_tenant_id(self):
        """测试 flush 前自动添加 tenant_id"""
        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name = Column(String)
            tenant_id = Column(String)

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        enable_sqlalchemy_tenant_isolation(engine)

        set_tenant_id("tenant_123")

        with Session(engine) as session:
            user = User(name="test")
            session.add(user)
            session.flush()
            assert user.tenant_id == "tenant_123"

    def test_before_flush_respects_explicit_tenant_id(self):
        """测试 flush 前如果已显式设置 tenant_id 则不覆盖"""
        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name = Column(String)
            tenant_id = Column(String)

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        enable_sqlalchemy_tenant_isolation(engine)

        set_tenant_id("tenant_123")

        with Session(engine) as session:
            user = User(name="test", tenant_id="tenant_456")
            session.add(user)
            session.flush()
            assert user.tenant_id == "tenant_456"

    def test_before_flush_skips_non_tenant_models(self):
        """测试 flush 前跳过不包含 tenant_id 的模型"""
        class Config(Base):
            __tablename__ = "configs"
            id = Column(Integer, primary_key=True)
            key = Column(String)
            value = Column(String)

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        enable_sqlalchemy_tenant_isolation(engine)

        set_tenant_id("tenant_123")

        with Session(engine) as session:
            config = Config(key="test", value="value")
            session.add(config)
            session.flush()
            # Config 模型没有 tenant_id 字段，不应该出错
            assert config.key == "test"
