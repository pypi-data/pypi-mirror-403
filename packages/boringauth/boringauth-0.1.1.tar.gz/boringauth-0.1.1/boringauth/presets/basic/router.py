from fastapi import APIRouter, Depends, Response, HTTPException, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from .service import AuthService
from .schemas import LoginUserSchema,CreateUserSchema
from .database import get_db
from .service import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", status_code=201)
def register(
    payload: CreateUserSchema,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    existing = service.repo.get_user_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    service.create_user(payload)
    return {"message": "User registered successfully"}


@router.post("/login")
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    user = service.authenticate_user(
        LoginUserSchema(
            email=form_data.username,
            password=form_data.password,
        )
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access, refresh = service.generate_tokens(str(user.id))

    response.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        samesite="lax",
    )

    return {"message": "Logged in"}


@router.post("/refresh")
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401)

        user_id = payload["sub"]

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    service = AuthService(db)
    access, _ = service.generate_tokens(user_id)

    response.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        samesite="lax",
    )

    return {"message": "Token refreshed"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}