"""
Database connections and initialization
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from app.core.settings import settings
from app.models.user import Base


class DatabaseManager:
    """Manages database connections"""
    
    def __init__(self):
        self.mongo_client: AsyncIOMotorClient | None = None
        self.mongo_db: AsyncIOMotorDatabase | None = None
        self.redis_client: Redis | None = None
        self.postgres_engine: AsyncEngine | None = None
        self.async_session_maker: async_sessionmaker[AsyncSession] | None = None
    
    async def connect_postgres(self):
        """Connect to PostgreSQL and create tables"""
        # Convert postgresql:// to postgresql+asyncpg://
        async_url = settings.postgres_url.replace("postgresql://", "postgresql+asyncpg://")
        
        self.postgres_engine = create_async_engine(
            async_url,
            echo=False,  # Set to True for SQL query logging
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        
        # Create async session factory
        self.async_session_maker = async_sessionmaker(
            self.postgres_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create all tables
        async with self.postgres_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✓ Connected to PostgreSQL")
    
    async def connect_mongo(self):
        """Connect to MongoDB"""
        self.mongo_client = AsyncIOMotorClient(settings.mongo_url)
        # Extract database name from URL or use default
        self.mongo_db = self.mongo_client.clarity
        
        # Create indexes
        await self.mongo_db.journal_entries.create_index("user_id")
        await self.mongo_db.journal_entries.create_index("created_at")
        
        print("✓ Connected to MongoDB")
    
    def connect_redis(self):
        """Connect to Redis"""
        self.redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        # Test connection
        self.redis_client.ping()
        print("✓ Connected to Redis")
    
    async def disconnect_postgres(self):
        """Disconnect from PostgreSQL"""
        if self.postgres_engine is not None:
            await self.postgres_engine.dispose()
            print("✓ Disconnected from PostgreSQL")
    
    async def disconnect_mongo(self):
        """Disconnect from MongoDB"""
        if self.mongo_client is not None:
            self.mongo_client.close()
            print("✓ Disconnected from MongoDB")
    
    def disconnect_redis(self):
        """Disconnect from Redis"""
        if self.redis_client is not None:
            self.redis_client.close()
            print("✓ Disconnected from Redis")
    
    def get_postgres_session(self) -> AsyncSession:
        """Get PostgreSQL session"""
        if self.async_session_maker is None:
            raise RuntimeError("PostgreSQL not connected")
        return self.async_session_maker()
    
    def get_mongo_db(self) -> AsyncIOMotorDatabase:
        """Get MongoDB database instance"""
        if self.mongo_db is None:
            raise RuntimeError("MongoDB not connected")
        return self.mongo_db
    
    def get_redis(self) -> Redis:
        """Get Redis client instance"""
        if self.redis_client is None:
            raise RuntimeError("Redis not connected")
        return self.redis_client


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncSession:
    """Dependency to get PostgreSQL session"""
    async with db_manager.get_postgres_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency to get MongoDB database"""
    return db_manager.get_mongo_db()


def get_redis_client() -> Redis:
    """Dependency to get Redis client"""
    return db_manager.get_redis()
