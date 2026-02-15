from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.logger import get_logger
from .core.db import engine, Base
from .core.di import container
from .api import health, user, chat, analysis

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Clarity Couple API...")
    
    # Initialize DB tables (for dev simplicity, use migrations in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Initialize DI Container
    container.init_services()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:5173", # Vite default
        "https://cc.rima-app.com",
        "https://www.cc.rima-app.com",
        "https://becc.rima-app.com",
        "https://www.becc.rima-app.com"
    ], 
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router)
app.include_router(user.router)
app.include_router(chat.router) 
app.include_router(analysis.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 

