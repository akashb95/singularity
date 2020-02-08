import logging

from sqlalchemy.orm import sessionmaker

from dbHandler import engine
from lighting.lib.user_pb2_grpc import UserServicer
from log import setup_logger


class UserHandler(UserServicer):
    MAX_LIST_SIZE = 1000

    def __init__(self):
        self.db = sessionmaker(bind=engine)()
        self.logger = setup_logger("telecellHandler", logging.DEBUG)
        return

    def Get(self, request, context):
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
