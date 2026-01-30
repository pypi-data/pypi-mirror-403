from sqlalchemy.orm import create_engine,DeclarativeBase,sessionmaker,create_engine
from .models import 
class Base(DeclarativeBase):
    pass

engine = create_engine('sqlite:///',echo=True)

def get_db():
    try:
        db = sessionmaker(auto_flush=False,auto_commit=False,bind=engine)
        yield db
    finally:
        db.close()
