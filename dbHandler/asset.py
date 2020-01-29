from sqlalchemy import Column, Integer

from dbHandler import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
