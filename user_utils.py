from db_utils import Base
from sqlalchemy import Column, String
from passlib.context import CryptContext

pwd_cxt = CryptContext(schemes=['bcrypt'], deprecated="auto")

class Hash():
    def bcrypt(password: str):
        return pwd_cxt.hash(password)

    def verify(plain_password: str, hashed_password: str):
        return pwd_cxt.verify(plain_password, hashed_password)

class DBUsers(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    username = Column(String)
    password = Column(String)
    email = Column(String)