from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import db_manager
from app.routes import journal, auth, analytics, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Clarity API...")
    await db_manager.connect_postgres()
    await db_manager.connect_mongo()
    db_manager.connect_redis()
    print("✓ All connections established")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Clarity API...")
    await db_manager.disconnect_postgres()
    await db_manager.disconnect_mongo()
    db_manager.disconnect_redis()
    print("✓ All connections closed")


app = FastAPI(
    title="Clarity API",
    description="Mental health journaling and analysis API",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(journal.router)
app.include_router(analytics.router)
app.include_router(search.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "clarity-api"}
