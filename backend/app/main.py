import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import admin, auth, leaderboard, scores
from app.core.config import settings
from app.core.limiter import limiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("showscore")

app = FastAPI(
    title="showScore API",
    description="Real-time leaderboard system powered by FastAPI, PostgreSQL and Redis.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


app.include_router(auth.router)
app.include_router(scores.router)
app.include_router(leaderboard.router)
app.include_router(admin.router)


@app.get("/api/health", tags=["health"])
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/", tags=["health"])
async def root():
    return {"service": "showScore", "status": "running"}
