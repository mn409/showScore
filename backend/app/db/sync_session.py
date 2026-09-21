from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

sync_engine = create_engine(settings.SYNC_DATABASE_URL, pool_pre_ping=True, future=True)
SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False, expire_on_commit=False)
