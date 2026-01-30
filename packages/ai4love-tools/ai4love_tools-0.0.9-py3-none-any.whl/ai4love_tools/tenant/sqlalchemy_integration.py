"""
SQLAlchemy ORM 自动租户过滤集成

在不改动业务代码的前提下，自动为包含 tenant_id 字段的模型追加租户过滤。
"""

from typing import Any

try:
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session, sessionmaker
    from sqlalchemy.orm.decl_api import DeclarativeMeta
    from sqlalchemy.sql import Select
    try:
        from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
    except ImportError:
        AsyncEngine = None
        AsyncSession = None
        async_sessionmaker = None
except ImportError:
    event = None
    Engine = None
    Session = None
    sessionmaker = None
    DeclarativeMeta = None
    Select = None
    AsyncSession = None
    async_sessionmaker = None
    AsyncEngine = None

from ai4love_tools.tenant.context import get_tenant_id
from ai4love_tools.tenant.exceptions import TenantIdMissingError

# 模型元数据缓存：记录哪些模型包含 tenant_id 字段
_model_tenant_cache: dict[type, bool] = {}


def _has_tenant_column(model_class: type) -> bool:
    """
    检查模型类是否包含租户字段

    Args:
        model_class: SQLAlchemy 模型类

    Returns:
        如果模型包含 tenant_id 字段则返回 True
    """
    if model_class in _model_tenant_cache:
        return _model_tenant_cache[model_class]

    if not hasattr(model_class, "__table__"):
        _model_tenant_cache[model_class] = False
        return False

    table = model_class.__table__
    has_tenant = "tenant_id" in table.columns

    _model_tenant_cache[model_class] = has_tenant
    return has_tenant


def _should_apply_tenant_filter(
    model_class: type | None, enabled_models: set[type] | None = None
) -> bool:
    """
    判断是否应该应用租户过滤

    Args:
        model_class: 模型类
        enabled_models: 启用租户过滤的模型白名单，如果为 None 则对所有包含 tenant_id 的模型启用

    Returns:
        是否应该应用租户过滤
    """
    if not model_class:
        return False

    if enabled_models is not None:
        return model_class in enabled_models

    return _has_tenant_column(model_class)


def _add_tenant_filter_to_select(
    select_stmt: Select, model_class: type, tenant_id: str | int
) -> Select:
    """
    为 SELECT 语句添加租户过滤条件

    Args:
        select_stmt: SQLAlchemy Select 语句
        model_class: 模型类
        tenant_id: 租户ID

    Returns:
        添加了租户条件的 Select 语句
    """
    if not _should_apply_tenant_filter(model_class):
        return select_stmt

    # 检查是否已有租户条件
    for criterion in select_stmt.whereclause.children if select_stmt.whereclause else []:
        if hasattr(criterion, "left") and hasattr(criterion.left, "key"):
            if criterion.left.key == "tenant_id":
                return select_stmt

    # 添加租户条件
    tenant_column = getattr(model_class, "tenant_id", None)
    if tenant_column is None:
        return select_stmt

    return select_stmt.where(tenant_column == tenant_id)


def _before_flush_add_tenant_id_async(session: Any, flush_context: Any, instances: Any) -> None:
    """
    在 flush 前自动为 INSERT 操作补充 tenant_id（异步版本）

    Args:
        session: SQLAlchemy AsyncSession
        flush_context: flush 上下文
        instances: 实例列表
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return

    for instance in session.new:
        if not hasattr(instance, "__class__"):
            continue

        model_class = instance.__class__
        if not _should_apply_tenant_filter(model_class):
            continue

        if hasattr(instance, "tenant_id") and getattr(instance, "tenant_id", None) is None:
            setattr(instance, "tenant_id", tenant_id)


def _before_flush_add_tenant_id(session: Session, flush_context: Any, instances: Any) -> None:
    """
    在 flush 前自动为 INSERT 操作补充 tenant_id

    Args:
        session: SQLAlchemy Session
        flush_context: flush 上下文
        instances: 实例列表
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return

    for instance in session.new:
        if not hasattr(instance, "__class__"):
            continue

        model_class = instance.__class__
        if not _should_apply_tenant_filter(model_class):
            continue

        if hasattr(instance, "tenant_id") and getattr(instance, "tenant_id", None) is None:
            setattr(instance, "tenant_id", tenant_id)


def enable_sqlalchemy_tenant_isolation(
    engine_or_session_factory: Any,
    *,
    tenant_column: str = "tenant_id",
    require_tenant: bool = False,
    enabled_models: set[type] | None = None,
) -> None:
    """
    启用 SQLAlchemy ORM 自动租户过滤

    支持同步和异步 SQLAlchemy。

    在应用启动阶段调用一次即可全局生效。

    Args:
        engine_or_session_factory: SQLAlchemy Engine、AsyncEngine、sync_engine（AsyncEngine.sync_engine）、
                                  sessionmaker、async_sessionmaker 或 Session/AsyncSession 类
        tenant_column: 租户字段名，默认 "tenant_id"
        require_tenant: 是否强制要求上下文中有租户ID，默认 False
        enabled_models: 启用租户过滤的模型白名单，如果为 None 则对所有包含 tenant_id 的模型启用

    Example:
        # 同步引擎
        from sqlalchemy import create_engine
        from ai4love_tools.tenant.sqlalchemy_integration import enable_sqlalchemy_tenant_isolation

        engine = create_engine("sqlite:///db.sqlite")
        enable_sqlalchemy_tenant_isolation(engine)

        # 异步引擎（方式1：传入 AsyncEngine）
        from sqlalchemy.ext.asyncio import create_async_engine
        async_engine = create_async_engine("sqlite+aiosqlite:///db.sqlite")
        enable_sqlalchemy_tenant_isolation(async_engine)

        # 异步引擎（方式2：传入 sync_engine，就像日志代码一样）
        async_engine = create_async_engine("sqlite+aiosqlite:///db.sqlite")
        enable_sqlalchemy_tenant_isolation(async_engine.sync_engine)
    """
    if event is None:
        raise ImportError("SQLAlchemy 未安装，无法启用租户隔离功能")

    # 注意：虽然可以传入 AsyncEngine 或 sync_engine（如 self.engine.sync_engine），
    # 但 do_orm_execute 是 Session 级别的事件，必须注册在 Session 类上，不能注册在 Engine 上
    # 这与 before_cursor_execute/after_cursor_execute 不同，后者是 Engine 级别的事件，可以在 sync_engine 上注册

    # 注册 before_flush 事件（用于 INSERT）
    # 注意：AsyncSession 不支持 before_flush 事件，只注册同步 Session
    if Session is not None:
        # 同步 Session
        try:
            listeners = event.contains(Session, "before_flush", _before_flush_add_tenant_id)
            if not listeners:
                event.listen(Session, "before_flush", _before_flush_add_tenant_id)
        except (AttributeError, TypeError):
            event.listen(Session, "before_flush", _before_flush_add_tenant_id)

    # 对于异步 Session，INSERT 操作的 tenant_id 需要在业务代码中手动设置
    # 或者通过 do_orm_execute 钩子在 UPDATE/DELETE 时处理
    # 注意：AsyncSession 不支持 before_flush 事件

    # 对于 SQLAlchemy 2.0+，使用 do_orm_execute 钩子
    # 注意：AsyncSession 不支持 do_orm_execute 事件，只注册同步 Session
    try:
        from sqlalchemy.orm import ORMExecuteState

        if Session is not None:
            # 同步 Session 的 do_orm_execute
            # 注意：在 SQLAlchemy 2.0+ 中，这个事件也会被 AsyncSession 使用（通过内部同步 Session）
            @event.listens_for(Session, "do_orm_execute", once=False)
            def _do_orm_execute(state: ORMExecuteState) -> None:
                """
                在执行 ORM 查询时自动添加租户过滤

                注意：这个事件监听器注册在 Session 类上，在 SQLAlchemy 2.0+ 中，
                AsyncSession 内部也会使用同步 Session，因此这个事件也会被触发
                """
                tenant_id = get_tenant_id()

                if require_tenant and not tenant_id:
                    raise TenantIdMissingError("执行 ORM 查询需要租户ID，但上下文中未设置")

                if not tenant_id:
                    return

                if not isinstance(state.statement, Select):
                    return

                # 获取查询涉及的模型
                for entity in state.statement.column_descriptions:
                    if "entity" in entity:
                        model_class = entity["entity"]
                        if _should_apply_tenant_filter(model_class, enabled_models):
                            state.statement = _add_tenant_filter_to_select(
                                state.statement, model_class, tenant_id
                            )
                            break

    except ImportError:
        # SQLAlchemy 1.x 版本，使用其他方式
        pass
