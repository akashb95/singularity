from datetime import datetime

from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, backref

from dbHandler import Base
from lighting.lib import telecell_pb2
from .basestation import Basestation


class Telecell(Base):
    __tablename__ = "telecell"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(Integer, unique=True, nullable=False)
    relay = Column(Boolean)
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(Integer, default=telecell_pb2.ActivityStatus.Value("INACTIVE"))
    updated_at = Column(DateTime, nullable=False, default=func.utc_timestamp())

    # a telecell has 1 basestation at a time, but each basestation is connected to multiple telecells
    bs_id = Column(Integer, ForeignKey("basestation.id"), nullable=True)
    basestation = relationship(Basestation, backref=backref("telecells", uselist=True))

    def __init__(self, uuid: int, relay: bool, latitude: float = None, longitude: float = None, basestation=None,
                 status: int = None, updated_at: datetime = None):

        self.uuid = uuid
        self.relay = relay

        if latitude:
            self.latitude = latitude

        if longitude:
            self.longitude = longitude

        if basestation:
            self.basestation = basestation

        if status is not None:
            self.status = status

        if updated_at is not None:
            self.updated_at = updated_at

        return
