from sqlalchemy import Column,String,Integer
from .database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
class UserModel(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    email = Column(String,unique=True,nullable=False,index=True)
    password = Column(String, nullable=False)
