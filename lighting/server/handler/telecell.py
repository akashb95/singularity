import logging

from sqlalchemy.orm import sessionmaker

from dbHandler import engine
from lighting.lib.telecell_pb2_grpc import TelecellServicer
from log import setup_logger


class TelecellHandler(TelecellServicer):
    MAX_LIST_SIZE = 50

    def __init__(self):
        self.db = sessionmaker(bind=engine)()
        self.logger = setup_logger("telecellHandler", logging.DEBUG)
        return

    def Get(self, request, context):
        return

    def List(self, request, context):
        return

    def SearchByLocation(self, request, context):
        return

    def Create(self, request, context):
        return

    def Update(self, request, context):
        return

    def Delete(self, request, context):
        return

    def AddToElement(self, request, context):
        return

    def RemoveFromElement(self, request, context):
        return
