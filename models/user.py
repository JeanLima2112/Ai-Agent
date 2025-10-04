from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    
    def __init__(self, email: str, password: str, active: bool = True):
        self.email = email
        self.password = password
        self.active = active
        
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
