from datetime import datetime, timedelta, timezone
from jose import jwt
import bcrypt

from .repository import AuthRepository
from .schemas import CreateUserSchema, LoginUserSchema

SECRET_KEY = "CHANGE_ME"
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthService:
    def __init__(self, db):
        self.repo = AuthRepository(db)

    # ---------- password ----------
    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(
            plain.encode("utf-8"),
            hashed.encode("utf-8"),
        )

    # ---------- tokens ----------
    def create_token(self, data: dict, expires: timedelta):
        payload = data.copy()
        payload["exp"] = datetime.now(timezone.utc) + expires
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def generate_tokens(self, user_id: str):
        access = self.create_token(
            {"sub": user_id, "type": "access"},
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh = self.create_token(
            {"sub": user_id, "type": "refresh"},
            timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return access, refresh

    # ---------- core ----------
    def create_user(self, payload: CreateUserSchema):
        hashed = self.hash_password(payload.password)
        return self.repo.create_user(payload.email, hashed)

    def authenticate_user(self, payload: LoginUserSchema):
        user = self.repo.get_user_by_email(payload.email)
        if not user:
            return None

        if not self.verify_password(payload.password, user.password):
            return None

        return user
