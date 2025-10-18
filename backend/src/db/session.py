from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/online_doc"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with SessionLocal() as session:
        yield session
