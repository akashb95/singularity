import logging

from sqlalchemy.orm import sessionmaker

import lighting.lib.user_pb2 as user_pb2
from dbHandler import User, engine
from lighting.lib.user_pb2_grpc import UserServicer
from log import setup_logger


class UserHandler(UserServicer):
    MAX_LIST_SIZE = 1000

    def __init__(self):
        self.db = sessionmaker(bind=engine)()
        self.logger = setup_logger("userHandler", logging.DEBUG)
        return

    def Get(self, request, context):
        """
        Gets User from DB by ID or by username.

        :param request:
        :param context:
        :return:
        """

        if request.id:
            user = self.db.query(User).get(request.id)

        elif request.username:
            user = self.db.query(User).filter(User.username == request.username)

        else:
            user = None

        # sanity checks
        if not user:
            if request.id:
                message = "Could not find User with ID {}".format(request.id)
            elif request.username:
                message = "Could not find User with username {}".format(request.username)
            else:
                message = "Expected to have User ID or username -- none passed in as params in procedure call."

            # empty reply
            self.logger.info(message)
            context.set_details(message)
            return user_pb2.Reply()

        # debugging info
        message = "Request for user with {}: {}" \
            .format("ID" if request.id else "username",
                    user.id if request.id else request.username)
        self.logger.info(message)

        user_message = user_pb2.Reply(id=user.id,
                                      username=user.username,
                                      hashed_pass=user.hashed_pass,
                                      role=user.role,
                                      created=user.created)

        return user_message

    def Create(self, request, context):
        """
        Inserts new User in DB.

        :param request:
        :param context:
        :return:
        """

        # don't let default value for user be the zero value
        if request.role == 0:
            role = user_pb2.Role.Value("ADMIN")

        else:
            role = request.role

        user = User(username=request.username, hashed_pass=request.hashed_pass, role=role)
        self.db.commit()
        self.db.refresh(user)

        user_message = user_pb2.Reply(id=user.id,
                                      username=user.username,
                                      hashed_pass=user.hashed_pass,
                                      role=user.role,
                                      created=user.created)

        return user_message

    def Update(self, request, context):
        """
        Updates User details.

        Request needs to have user ID, as the user's username is changeable.

        :param request:
        :param context:
        :return:
        """

        # Sanity checks
        if request.id:
            user = self.db.query(User).get(request.id)

        else:
            user = None

        if not user:
            message = "Could not find User with ID {}".format(request.id)
            context.set_details(message)
            return user_pb2.Reply()

        # for logging
        message = "Updating user with ID {}... (Username: {}, Hash: {}, Role: {}) --> " \
            .format(user.id, user.username, user.hashed_pass, user_pb2.Role.Name(user.role))

        if request.username:
            user.username = request.username

        if request.hashed_pass:
            user.hashed_pass = request.hashed_pass

        if request.role:
            user.role = request.role

        self.db.commit()
        self.db.refresh(user)

        # for logging
        message += "(Username: {}, Hash: {}, Role: {})" \
            .format(user.username, user.hashed_pass, user_pb2.Role.Name(user.role))
        self.logger.info(message)

        user_message = user_pb2.Reply(
            id=user.id,
            username=user.username,
            hashed_pass=user.hashed_pass,
            role=user.role,
            created=user.created)

        return user_message

    def Delete(self, request, context):
        """
        Delete user permanently from DB.

        :param request:
        :param context:
        :return:
        """

        # Sanity checks
        if request.id:
            user = self.db.query(User).get(request.id)

        else:
            user = None

        if not user:
            message = "Could not find User with ID {}".format(request.id)
            context.set_details(message)
            return user_pb2.Reply()

        message = "Deleting User (ID: {}, Username: {})".format(user.id, user.username)

        # create message before details deleted...
        user_message = user_pb2.Reply(id=user.id, username=user.username,
                                      hashed_pass=user.hashed_pass, role=user.role,
                                      created=user.created)

        self.db.delete(user.id)
        self.db.commit()

        self.logger.info(message)

        return user_message
