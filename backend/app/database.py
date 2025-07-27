from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from sqlalchemy.orm import sessionmaker,declarative_base
from app.config import DATABASE_URL,SECRET_KEY
#db is chatdb/postgresql and user is postgres
engine=create_async_engine(DATABASE_URL,future=True,echo=False)# allows a system to perform operations 
#without blocking the main execution thread
AsyncSessionLocal=sessionmaker(engine,class_=AsyncSession,expire_on_commit=False)#creating an async session

Base=declarative_base()

if not DATABASE_URL or not SECRET_KEY: #error checkif missing key or db url
    raise RuntimeError("Missing critical environment variables")



#dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session