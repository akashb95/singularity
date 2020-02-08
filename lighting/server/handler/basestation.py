import logging

from sqlalchemy.orm import sessionmaker

from dbHandler import engine
from lighting.lib.basestation_pb2_grpc import BasestationServicer
from log import setup_logger


class BasestationHandler(BasestationServicer):
    MAX_LIST_SIZE = 1000

    def __init__(self):
        self.db = sessionmaker(bind=engine)()
        self.logger = setup_logger("basestationHandler", logging.DEBUG)
        return

    def Get(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        return

    def List(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        return

    def SearchByLocation(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        return

    def Create(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        return

    def Update(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        return

    def Delete(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        return
