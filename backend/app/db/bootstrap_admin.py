"""
Run once after migrations to create the first admin account:
    python -m app.db.bootstrap_admin
"""
import asyncio

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.services.auth_service import get_user_by_email


async def main() -> None:
    async with AsyncSessionLocal() as db:
        existing = await get_user_by_email(db, settings.FIRST_ADMIN_EMAIL)
        if existing:
            print(f"Admin '{settings.FIRST_ADMIN_EMAIL}' already exists. Skipping.")
            return

        admin = User(
            email=settings.FIRST_ADMIN_EMAIL,
            username="admin",
            password_hash=hash_password(settings.FIRST_ADMIN_PASSWORD),
            role=UserRole.admin,
        )
        db.add(admin)
        await db.commit()
        print(f"Created admin user: {settings.FIRST_ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(main())
