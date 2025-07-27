import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import Base  # Your Base with metadata
# IMPORTANT: Import your models here so they register with Base.metadata
from app.models import User, Message, Friendship  

DATABASE_URL = "postgresql+asyncpg://parth:mattap1567@localhost:5432/chatdb"

engine = create_async_engine(DATABASE_URL, echo=True)

async def create_tables():
    async with engine.begin() as conn:
        # This will now see the models and create tables
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
