from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, backref

from dbHandler import Base
from .basestation import Basestation


class Telecell(Base):
    __tablename__ = "telecells"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(Integer, unique=True, nullable=False)
    relay = Column(Boolean)
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(Integer, default=0)
    updated_at = Column(DateTime, nullable=False, default=func.now())

    # a telecell has 1 basestation at a time, but each basestation is connected to multiple telecells
    bs_id = Column(Integer, ForeignKey("basestations.id"))
    basestation = relationship(Basestation, backref=backref("telecells", uselist=True))

    def __init__(self, uuid, relay, latitude, longitude, basestation=None, status=None, updated_at=None):

        self.uuid = uuid
        self.relay = relay
        self.latitude = latitude
        self.longitude = longitude

        if basestation:
            self.basestation = basestation

        if status is not None:
            self.status = status

        if updated_at is not None:
            self.updated_at = updated_at

        return
