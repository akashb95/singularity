import logging

import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

import lighting.lib.basestation_pb2 as bs_pb2
from dbHandler import Basestation, engine
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

        message = ""

        if request.id:
            bs = self.db.query(Basestation).get(request.id)

        elif request.uuid:
            bs = self.db.query(Basestation).filter(Basestation.uuid == request.uuid).first()

        else:
            bs = None
            message = "Need to provide Basestation ID or UUID for this RPC."

        if not bs:
            if not message:
                message = "Basestation with {}: {} not found." \
                    .format("ID" if request.id else request.uuid,
                            request.id or request.uuid)

            self.logger.info(message)
            context.set_details(message)
            bs_message = bs_pb2.Reply(no_location=True)
            return bs_message

        bs_message = self._prepare_basestation_message(bs)
        return bs_message

    def List(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        self.logger.info("Request list of {} Basestations, offset by {}".format(request.limit, request.offset))

        # get all elements if no limit or offset specified.
        basestations = self.db.query(Basestation)

        if request.limit:
            basestations = basestations.limit(request.limit)

        if request.offset:
            basestations = basestations.offset(request.offset)

        basestations = basestations.all()

        replies = []

        for i, basestation in enumerate(basestations):
            bs_reply = self._prepare_basestation_message(basestation)
            replies.append(bs_reply)

            if len(replies) == self.MAX_LIST_SIZE or i == len(basestations) - 1:
                # populate outgoing message
                bs_reply_list = bs_pb2.ListReply()
                bs_reply_list.elements.extend(replies)

                # reset list for next batch of messages that'll go in the next stream
                replies = []

                # stream
                yield bs_reply_list

        return

    def SearchByLocation(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        # find the bounding box on the map
        left = min(request.rectangle.lo.long, request.rectangle.hi.long)
        right = max(request.rectangle.lo.long, request.rectangle.hi.long)
        top = max(request.rectangle.lo.lat, request.rectangle.hi.lat)
        bottom = min(request.rectangle.lo.lat, request.rectangle.hi.lat)

        self.logger.info(
            "Request for Basestations in box between ({}, {}) and ({}, {})".format(bottom, left, top, right))

        # find elements in that fall in bounding box
        basestations = self.db.query(Basestation) \
            .filter(
            db.and_(Basestation.longitude >= left, Basestation.longitude <= right,
                    Basestation.latitude >= bottom, Basestation.latitude <= top)) \
            .all()

        for basestation in basestations:
            bs_reply = self._prepare_basestation_message(basestation)

            # stream reply to client
            yield bs_reply

    def Create(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        if not request.uuid:
            message = "Creating Basestation failed: expected Basestation UUID."
            context.set_details(message)
            return bs_pb2.Reply(no_location=True)

        new_bs = Basestation(request.uuid)

        if not request.no_location:
            new_bs.latitude = request.location.latitude
            new_bs.longitude = request.location.longitude

        self.db.add(new_bs)
        self.db.commit()
        self.db.refresh(new_bs)

        bs_reply = self._prepare_basestation_message(new_bs)

        return bs_reply

    def Update(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        message = ""

        if request.id:
            bs = self.db.query(Basestation).get(request.id)

        elif request.uuid:
            bs = self.db.query(Basestation).filter(Basestation.uuid == request.uuid).first()

        else:
            bs = None
            message = "Need to provide Basestation ID or UUID for this RPC."

        if not bs:
            if not message:
                message = "Basestation with {}: {} not found." \
                    .format("ID" if request.id else request.uuid,
                            request.id or request.uuid)

            self.logger.info(message)
            context.set_details(message)
            bs_message = bs_pb2.Reply(no_location=True)
            return bs_message

        message = "Updating Basestation ({}, {}) (ID: {}, UUID: {}, version: {}, status: {}) --> " \
            .format(bs.latitude, bs.longitude, bs.id, bs.uuid, bs.version, bs_pb2.ActivityStatus.Name(bs.status))

        if request.version:
            bs.version = request.version

        if request.status:
            bs.status = request.status

        if not request.no_location and request.location:
            bs.latitude = request.location.latitude
            bs.longitude = request.location.longitude

        self.db.commit()

        message += "Basestation ({}, {}) (ID: {}, UUID: {}, version: {}, status: {})" \
            .format(bs.latitude, bs.longitude, bs.id, bs.uuid, bs.version, bs_pb2.ActivityStatus.Name(bs.status))
        self.logger.info(message)

        bs_reply = self._prepare_basestation_message(bs)

        return bs_reply

    def Delete(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        message = ""

        if request.id:
            bs = self.db.query(Basestation).get(request.id)

        elif request.uuid:
            bs = self.db.query(Basestation).filter(Basestation.uuid == request.uuid).first()

        else:
            bs = None
            message = "Need to provide Basestation ID or UUID for this RPC."

        if not bs:
            if not message:
                message = "Basestation with {}: {} not found." \
                    .format("ID" if request.id else request.uuid,
                            request.id or request.uuid)

            self.logger.info(message)
            context.set_details(message)
            bs_message = bs_pb2.Reply(no_location=True)
            return bs_message

        message = "(Soft-)Deleting Basestation {} (ver. {}) - setting status to 15.".format(bs.id, bs.version)
        bs.status = bs_pb2.ActivityStatus.Value("DELETED")

        self.db.commit()
        self.logger.info(message)
        bs_reply = self._prepare_basestation_message(bs)

        return bs_reply

    def Prune(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        message = ""

        if request.id:
            bs = self.db.query(Basestation).get(request.id)

        elif request.uuid:
            bs = self.db.query(Basestation).filter(Basestation.uuid == request.uuid).first()

        else:
            bs = None
            message = "Need to provide Basestation ID or UUID for this RPC."

        if not bs:
            if not message:
                message = "Basestation with {}: {} not found." \
                    .format("ID" if request.id else request.uuid,
                            request.id or request.uuid)

            self.logger.info(message)
            context.set_details(message)
            bs_message = bs_pb2.Reply(no_location=True)
            return bs_message

        message = "Deleting Basestation {} (UUID: {})".format(bs.id, bs.uuid)

        # prepare reply before deleting from DB.
        bs_reply = bs_pb2.Reply(id=bs.id, uuid=bs.uuid, no_location=True)
        self.logger.info(message)

        self.db.delete(bs)
        self.db.commit()

        return bs_reply

    @staticmethod
    def _prepare_basestation_message(basestation: Basestation):
        """
        Given a row from the basestation table, populate the lighting.basestation.Reply message.

        This function checks also for whether the location has been set, and contains the logic to correctly populate
        the reply.

        :param basestation:
        :return:
        """

        bs_reply = bs_pb2.Reply(id=basestation.id, uuid=basestation.uuid,
                                version=basestation.version, status=basestation.status)

        if basestation.latitude is None or basestation.longitude is None:
            bs_reply.no_location = True

        else:
            bs_reply.location.latitude, bs_reply.location.longitude = basestation.latitude, basestation.longitude

        return bs_reply
