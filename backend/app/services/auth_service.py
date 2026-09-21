from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import UserRegister


class AuthError(Exception):
    pass


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, data: UserRegister) -> User:
    if await get_user_by_email(db, data.email):
        raise AuthError("Email already registered")
    if await get_user_by_username(db, data.username):
        raise AuthError("Username already taken")

    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        role=UserRole.user,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user
