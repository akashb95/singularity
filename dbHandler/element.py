from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship, backref

from dbHandler import Base
from .asset import Asset
from .telecell import Telecell


class Element(Base):
    __tablename__ = "elements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column("description", String(100))
    latitude = Column("latitude", Float, default=None)
    longitude = Column("longitude", Float, default=None)
    status = Column("status", Integer, default=0, nullable=False)

    # each element can have a maximum one 1 telecell
    telecell_id = Column(Integer, ForeignKey("telecells.id"))
    telecell = relationship(Telecell, backref=backref('elements', uselist=True))

    # 1 element/lamp has 1 asset/lamppost
    asset_id = Column(Integer, ForeignKey("assets.id"))
    asset = relationship(Asset, backref=backref("elements", uselist=True))

    def __init__(self, description: str, latitude: float, longitude: float, status: int, asset, telecell=None):
        self.description = description
        self.latitude = latitude
        self.longitude = longitude
        self.status = status

        self.asset = asset

        if telecell is not None:
            self.telecell = telecell

        return
