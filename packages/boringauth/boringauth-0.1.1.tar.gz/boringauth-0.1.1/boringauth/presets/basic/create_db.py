from .database import Base, engine
from .models import UserModel
Base.metadata.create_all(bind=engine)