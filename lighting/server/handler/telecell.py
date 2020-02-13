import logging
from datetime import datetime
from datetime import timezone

import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

import lighting.lib.telecell_pb2 as tc_pb2
from dbHandler import Telecell, engine
from lighting.lib.telecell_pb2_grpc import TelecellServicer
from log import setup_logger
from .basestation import BasestationHandler
from .element import ElementHandler


class TelecellHandler(TelecellServicer):
    MAX_LIST_SIZE = 50

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

        message = ""

        if request.id:
            tc = self.db.query(Telecell).get(request.id)

        elif request.uuid:
            tc = self.db.query(Telecell).filter(Telecell.uuid == request.uuid).first()

        else:
            tc = None
            message = "Need to provide Telecell ID or UUID for this RPC."

        if not tc:
            if not message:
                message = "Telecell with {}: {} not found." \
                    .format("ID" if request.id else "UUID",
                            request.id or request.uuid)

            self.logger.info(message)
            context.set_details(message)
            tc_message = tc_pb2.Reply(no_location=True)
            return tc_message

        tc_message = self.prepare_telecell_message(tc)

        return tc_message

    def List(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        telecells = self.db.query(Telecell)

        if request.limit:
            telecells = telecells.limit(request.limit)

        if request.offset:
            telecells = telecells.offset(request.offset)

        telecells = telecells.all()

        replies = []

        for i, tc in enumerate(telecells):
            tc_reply = self.prepare_telecell_message(tc)
            replies.append(tc_reply)

            if len(replies) == self.MAX_LIST_SIZE or i == len(telecells) - 1:
                # populate outgoing message
                tc_reply_list = tc_pb2.ListReply()
                tc_reply_list.telecells.extend(replies)

                # reset list for next batch of messages that'll go in the next stream
                replies = []

                # stream
                yield tc_reply_list
        return

    def SearchByLocation(self, request, context):
        # find the bounding box on the map
        left = min(request.rectangle.lo.long, request.rectangle.hi.long)
        right = max(request.rectangle.lo.long, request.rectangle.hi.long)
        top = max(request.rectangle.lo.lat, request.rectangle.hi.lat)
        bottom = min(request.rectangle.lo.lat, request.rectangle.hi.lat)

        self.logger.info(
            "Request for Basestations in box between ({}, {}) and ({}, {})".format(bottom, left, top, right))

        # find elements in that fall in bounding box
        telecells = self.db.query(Telecell) \
            .filter(db.and_(Telecell.longitude >= left, Telecell.longitude <= right,
                            Telecell.latitude >= bottom, Telecell.latitude <= top)) \
            .all()

        for tc in telecells:
            tc_reply = self.prepare_telecell_message(tc)

            # stream reply to client
            yield tc_reply

    def Create(self, request, context):
        """
        Creates new Telecell.

        But does NOT create new Element or Asset. Any details provided pertaining to those entities will be ignored.

        :param request:
        :param context:
        :return:
        """

        if not request.uuid:
            message = "Creating Telecell failed: expected Telecell UUID."
            self.logger.warn(message)
            context.set_details(message)
            return tc_pb2.Reply(no_location=True)

        longitude, latitude = None, None
        if not request.location.no_location:
            longitude, latitude = request.location.long, request.location.lat

        new_telecell = Telecell(uuid=request.uuid, latitude=latitude, longitude=longitude,
                                relay=request.relay, status=request.status)

        self.db.add(new_telecell)
        self.db.commit()

        return

    def Update(self, request, context):
        """
        Update details of Telecell.

        This does NOT allow user to update details of connected Basestations or Elements.

        :param request:
        :param context:
        :return:
        """

        message = ""

        if request.id:
            tc = self.db.query(Telecell).get(request.id)

        elif request.uuid:
            tc = self.db.query(Telecell).filter(Telecell.uuid == request.uuid).first()

        else:
            tc = None
            message = "Need to provide Telecell ID or UUID for this RPC."

        if not tc:
            if not message:
                message = "Telecell with {}: {} not found." \
                    .format("ID" if request.id else "UUID",
                            request.id or request.uuid)

            self.logger.info(message)
            context.set_details(message)
            tc_message = tc_pb2.Reply(no_location=True)
            return tc_message

        if request.relay:
            tc.relay = request.relay

        if request.status:
            tc.status = request.status

        # if no time provided by user, then just go ahead and save current server time as updated_at
        if request.updated_at.seconds:
            tc.updated_at = request.updated_at.seconds
        else:
            tc.updated_at = datetime.utcnow().timestamp()

        if not request.no_location:
            tc.longitude, tc.latitude = request.location.long, request.location.lat

        self.db.commit()
        self.db.refresh(tc)

        tc_reply = self.prepare_telecell_message(tc)

        return tc_reply

    def Delete(self, request, context):
        """
        Soft-delete a Telecell from the system by setting its Status to the appropriate value.

        :param request:
        :param context:
        :return:
        """

        message = ""

        if request.id:
            tc = self.db.query(Telecell).get(request.id)

        elif request.uuid:
            tc = self.db.query(Telecell).filter(Telecell.uuid == request.uuid).first()

        else:
            tc = None
            message = "Need to provide Telecell ID or UUID for this RPC."

        if not tc:
            if not message:
                message = "Telecell with {}: {} not found." \
                    .format("ID" if request.id else "UUID",
                            request.id or request.uuid)

            self.logger.info(message)
            context.set_details(message)
            tc_message = tc_pb2.Reply(no_location=True)
            return tc_message

        tc.status = tc_pb2.ActivityStatus.Value("DELETED")

        self.db.commit()
        self.db.refresh(tc)

        tc_reply = self.prepare_telecell_message(tc)

        return tc_reply

    def Prune(self, request, context):
        """
        Permanently delete Telecell from system.

        :param request:
        :param context:
        :return:
        """

        message = ""

        if request.id:
            tc = self.db.query(Telecell).get(request.id)

        elif request.uuid:
            tc = self.db.query(Telecell).filter(Telecell.uuid == request.uuid).first()

        else:
            tc = None
            message = "Need to provide Telecell ID or UUID for this RPC."

        if not tc:
            if not message:
                message = "Telecell with {}: {} not found." \
                    .format("ID" if request.id else "UUID",
                            request.id or request.uuid)

            self.logger.info(message)
            context.set_details(message)
            tc_message = tc_pb2.Reply(no_location=True)
            return tc_message

        tc_reply = tc_pb2.Reply(id=request.id, uuid=request.uuid, no_location=True)

        self.db.delete(tc)
        self.db.commit()

        return tc_reply

    @staticmethod
    def prepare_telecell_message(telecell: Telecell) -> tc_pb2.Reply:
        """
        Given a retrieved row from the telecell table in the DB, populate a lighting.telecell.Reply message accordingly.

        :param telecell:
        :return:
        """

        # create reply message and set up the fields with simple types
        tc_reply = tc_pb2.Reply(id=telecell.id, uuid=telecell.uuid, relay=telecell.relay, status=telecell.status)

        # set timestamp field
        tc_reply.updated_at.seconds = int(telecell.updated_at.replace(tzinfo=timezone.utc).timestamp())

        # set location or set no_location flag to True
        if telecell.latitude is not None and telecell.longitude is not None:
            tc_reply.location.long, tc_reply.location.lat = telecell.longitude, telecell.latitude
        else:
            tc_reply.no_location = True

        # set up BS field
        bs_reply = BasestationHandler.prepare_basestation_message(telecell.basestation)
        tc_reply.basestation = bs_reply

        # set up Elements field
        element_replies = []
        for element in telecell.elements:
            element_replies.append(ElementHandler.prepare_element_message(element))
        tc_reply.elements.extend(element_replies)

        return tc_reply
