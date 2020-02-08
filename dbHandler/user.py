from sqlalchemy import Column, Integer, String, DateTime, func

from dbHandler import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(25), nullable=False, unique=True)
    hashed_pass = Column(String(200), nullable=False)
    role = Column(Integer, nullable=False, default=2)
    created = Column(DateTime, default=func.utc_timestamp(), nullable=False)

    def __init__(self, username, hashed_pass, role):
        self.username = username
        self.hashed_pass = hashed_pass
        self.role = role
        return
