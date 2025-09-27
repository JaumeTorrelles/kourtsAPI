from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

# Synchronous engine for Alembic migrations
engine = create_engine(
    settings.database_url.replace("+asyncpg", ""),
    echo=settings.debug
)

# Asynchronous engine for the application
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300
)

# Asynchronous session factory
async_session = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_session() -> AsyncSession:
    """Dependency that provides database session for FastAPI endpoints."""
    async with async_session() as session:
        yield session

def create_db_and_tables() -> None:
    """Create all database tables (used by Alembic for initial setup)."""
    SQLModel.metadata.create_all(engine)
