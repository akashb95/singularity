from sqlalchemy import Column, String, Integer, Float
from dbHandler import Base


class Element(Base):
    __tablename__ = "elements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column("description", String(100))
    latitude = Column("latitude", Float)
    longitude = Column("longitude", Float)
    status = Column("status", Integer)

    def __init__(self, description: str, latitude: float, longitude: float, status: int):

        self.description = description
        self.latitude = latitude
        self.longitude = longitude
        self.status = status

        return
