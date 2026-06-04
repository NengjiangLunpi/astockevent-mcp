"""⚠️ STUB — async_session_factory.

完整实现仅在私有仓库 NengjiangLunpi/astockevent (PRIVATE) 中。

MCP Server (server.py) 通过 async_session_factory() 获取数据库会话。
本 Stub 抛出 NotImplementedError，仅供代码结构参考。
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

logger = logging.getLogger(__name__)


@asynccontextmanager
async def async_session_factory() -> AsyncGenerator[Any, None]:
    """⚠️ STUB: 创建异步数据库会话。

    完整实现使用 SQLAlchemy async engine + sessionmaker，连接 PostgreSQL。
    私有仓库中此函数返回一个 AsyncSession 实例。

    Raises:
        NotImplementedError: 本仓库为公开子集，数据库层仅在私有仓库中提供。
    """
    # TODO: 安装完整 astockevent 包后将自动获得真实实现
    # TODO: 或从私有仓库 NengjiangLunpi/astockevent 获取 db 模块覆盖此 Stub
    raise NotImplementedError(
        "Database layer is not available in the public subset. "
        "Full implementation is in the private repo: "
        "https://github.com/NengjiangLunpi/astockevent"
    )
