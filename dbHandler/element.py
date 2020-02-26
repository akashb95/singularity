from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref

from dbHandler import Base
from lighting.lib import element_pb2
from .telecell import Telecell


class Element(Base):
    __tablename__ = "element"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column("description", String(100), default="")
    status = Column("status", Integer, default=element_pb2.ActivityStatus.Value("INACTIVE"), nullable=False)

    # each element can have a maximum one 1 telecell
    telecell_id = Column(Integer, ForeignKey("telecell.id"), nullable=True)
    telecell = relationship(Telecell,
                            backref=backref("elements", uselist=True))

    # 1 element/lamp has 1 asset/lamppost
    asset_id = Column(Integer, ForeignKey("asset.id"), nullable=False)
    asset = relationship("Asset",
                         backref=backref("elements", cascade="merge, save-update, delete"))

    def __init__(self, asset, description: str = None, status: int = None, telecell=None):

        self.asset = asset

        if description is not None:
            self.description = description

        if self.status is not None:
            self.status = status

        if telecell is not None:
            self.telecell = telecell

        return
