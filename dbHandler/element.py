from sqlalchemy import Column, String, Integer, Float
from dbHandler import Base


class Element(Base):
    __tablename__ = "elements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column("description", String(100), default="")
    latitude = Column("latitude", Float, default=0.0)
    longitude = Column("longitude", Float, default=0.0)
    status = Column("status", Integer, default=0)

    def __init__(self, description: str, latitude: float, longitude: float, status: int):

        self.description = description
        self.latitude = latitude
        self.longitude = longitude
        self.status = status

        return
