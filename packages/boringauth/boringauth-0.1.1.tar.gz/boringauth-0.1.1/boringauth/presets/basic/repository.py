from sqlalchemy.orm import Session
from uuid import UUID

from .models import UserModel


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = UserModel

    def create_user(self, email: str, hashed_password: str) -> UserModel:
        user = self.model(
            email=email,
            password=hashed_password,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_email(self, email: str) -> UserModel | None:
        return (
            self.db.query(self.model)
            .filter(self.model.email == email)
            .first()
        )

    def get_user_by_id(self, user_id: UUID) -> UserModel | None:
        return (
            self.db.query(self.model)
            .filter(self.model.id == user_id)
            .first()
        )
