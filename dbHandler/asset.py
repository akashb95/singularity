from sqlalchemy import Column, Integer, Float

from dbHandler import Base
from lighting.lib import asset_pb2


class Asset(Base):
    __tablename__ = "asset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Integer, default=asset_pb2.ActivityStatus.Value("INACTIVE"))
    latitude = Column("latitude", Float, default=None)
    longitude = Column("longitude", Float, default=None)

    def __init__(self, status: int = None, latitude: float = None, longitude: float = None):

        if status:
            self.status = status

        if latitude is not None and longitude is not None:
            self.latitude = latitude
            self.longitude = longitude

        return
