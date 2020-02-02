from sqlalchemy import Column, Integer

from dbHandler import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Integer, default=1)

    def __init__(self, status: int = None):
        if status:
            self.status = status
        return
