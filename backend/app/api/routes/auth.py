from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_refresh_token
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import TokenPair, UserLogin, UserOut, UserRegister
from app.services.auth_service import AuthError, authenticate_user, register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        user = await register_user(db, payload)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return user


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id), user.role.value)
    _set_refresh_cookie(response, refresh_token)

    return TokenPair(access_token=access_token)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    response: Response,
    refresh_token: str = Depends(get_refresh_token),
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    role = payload.get("role")

    new_access = create_access_token(user_id, role)
    new_refresh = create_refresh_token(user_id, role)
    _set_refresh_cookie(response, new_refresh)

    return TokenPair(access_token=new_access)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/auth")
    return None


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
