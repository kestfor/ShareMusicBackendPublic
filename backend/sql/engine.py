from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from backend.config_reader import config

DATABASE = {
    'drivername': 'postgresql+asyncpg',  # Тут можно использовать MySQL или другой драйвер
    'host': config.sql_host.get_secret_value(),
    'port': config.sql_port.get_secret_value(),
    'username': config.sql_username.get_secret_value(),
    'password': config.sql_password.get_secret_value(),
    'database': config.sql_database.get_secret_value()
}

engine = create_async_engine(URL.create(**DATABASE), echo=True)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()
