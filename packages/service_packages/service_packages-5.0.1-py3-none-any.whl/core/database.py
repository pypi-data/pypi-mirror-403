from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.config.asyncio import AlembicAsyncConfig
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .settings import settings

config = SQLAlchemyAsyncConfig(
    connection_string=settings.db_url,
    metadata=UUIDAuditBase.metadata,
    create_all=settings.db_create_all,
    alembic_config=AlembicAsyncConfig(
        script_location="./migrations/",
    ),
)
sqlalchemy_plugin = SQLAlchemyPlugin(config=config)


engine = create_async_engine(settings.db_url, echo=False)
session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
