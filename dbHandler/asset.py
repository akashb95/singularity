from sqlalchemy import Column, Integer

from dbHandler import Base
from lighting.lib import asset_pb2


class Asset(Base):
    __tablename__ = "asset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Integer, default=asset_pb2.ActivityStatus.Value("INACTIVE"))

    def __init__(self, status: int = None):
        if status:
            self.status = status
        return
