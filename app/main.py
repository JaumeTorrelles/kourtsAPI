from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .core.database import async_engine
from .api.admin import router as admin_router
from .api.public import router as public_router
from sqlalchemy import text

app = FastAPI(
    title="Kourts API",
    description="Multi-sport Booking Manager as a Service",
    version="1.0.0"
)

# CORS middleware to allow direct calls from web applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP we allow all origins, can be restricted later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin_router)
app.include_router(public_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Kourts API!"}

@app.get("/health")
async def health_check():
    """Health check with database verification"""
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "healthy", 
            "service": "kourts",
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "service": "kourts", 
                "database": "disconnected",
                "error": str(e)
            }
        )

@app.on_event("startup")
async def startup_event():
    """Verify database connection on startup"""
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database connection verified")
    except Exception as e:
        print(f"Database connection error: {e}")
        # Don't stop the application, just show the error
