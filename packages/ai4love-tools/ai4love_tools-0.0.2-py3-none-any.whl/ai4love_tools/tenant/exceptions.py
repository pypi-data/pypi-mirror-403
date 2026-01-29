"""
租户隔离相关异常定义
"""


class TenantIsolationError(Exception):
    """租户隔离功能的基础异常类"""

    pass


class TenantIdMissingError(TenantIsolationError):
    """租户ID缺失异常"""

    def __init__(self, message: str = "租户ID未设置或缺失"):
        self.message = message
        super().__init__(self.message)


class UserIdMissingError(TenantIsolationError):
    """用户ID缺失异常"""

    def __init__(self, message: str = "用户ID未设置或缺失"):
        self.message = message
        super().__init__(self.message)


class SQLRewriteError(TenantIsolationError):
    """SQL重写错误异常"""

    def __init__(self, message: str = "SQL重写失败"):
        self.message = message
        super().__init__(self.message)
