from sqlalchemy import Column, Integer, Float

from dbHandler import Base


class Basestation(Base):
    __tablename__ = "basestation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(Integer, unique=True, nullable=False)
    version = Column(Integer, nullable=False, default=3)
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(Integer, default=0)

    def __init__(self, uuid: int, version: int, latitude: float = None, longitude: float = None, status: int = None):
        self.uuid = uuid
        self.version = version

        if latitude and longitude:
            self.latitude = latitude
            self.longitude = longitude

        if status is not None:
            self.status = status
        return
