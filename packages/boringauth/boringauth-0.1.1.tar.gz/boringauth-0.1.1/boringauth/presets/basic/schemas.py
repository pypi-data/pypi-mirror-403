from pydantic import BaseModel

class CreateUserSchema(BaseModel):
    email:str
    password:str

class LoginUserSchema(BaseModel):
    email:str
    password:str

