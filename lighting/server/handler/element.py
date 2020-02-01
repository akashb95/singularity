import logging
from log import setup_logger

import lighting.lib.element_pb2 as element_pb2
from lighting.lib.element_pb2_grpc import ElementServicer
from lighting.lib.location_pb2 import Location
import lighting.lib.asset_pb2 as asset_pb2

from lighting.server.helpers import activity_status_mapper

from dbHandler import Element, engine
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker


class ElementHandler(ElementServicer):
    MAX_LIST_SIZE = 50

    def __init__(self):
        self.db = sessionmaker(bind=engine)()
        self.logger = setup_logger("elementHandler", logging.DEBUG)
        return

    def Get(self, request, context):
        """
        Gets a single element by its unique id.

        :param request:
        :param context:
        :return:
        """

        self.logger.info("Request Element with ID of {}".format(request.id))

        element = self.db.query(Element).get(request.id)

        # if no element found
        if not element:
            return element_pb2.Reply()

        # if any of these fields empty, then gRPC will return the default value (0 for int, empty string for str, etc.)
        activity_status = activity_status_mapper(element.status)

        location = Location(lat=element.latitude, long=element.longitude)
        asset = asset_pb2.Reply(id=element.asset.id)

        return element_pb2.Reply(
            id=element.id,
            status=activity_status,
            location=location,
            asset=asset,
            description=element.description
        )

    def List(self, request, context):
        """
        Streams back lists of elements.

        Allows server-side definition of the largest each response stream can be. Prevents over-optimisation.

        :param request:
        :param context:
        :return:
        """

        self.logger.info("Request list of {} Elements, offset by {}".format(request.limit, request.offset))

        # get all elements if no limit or offset specified.
        elements = self.db.query(Element)

        if request.limit:
            elements = elements.limit(request.limit)

        if request.offset:
            elements = elements.offset(request.offset)

        elements = elements.all()

        replies = []

        for i, element in enumerate(elements):
            replies.append(
                element_pb2.Reply(
                    id=element.id,
                    status=activity_status_mapper(element.status),
                    location=Location(lat=element.latitude, long=element.longitude),
                    asset=asset_pb2.Reply(id=element.asset.id),
                    description=element.description)
            )

            if len(replies) == self.MAX_LIST_SIZE or i == len(elements) - 1:
                reply_list = element_pb2.ListReply()
                reply_list.elements.extend(replies)
                replies = []
                yield reply_list

    def SearchByLocation(self, request, context):
        """
        Search for elements based on a map rectangle.

        Need to define 2 sets of latitude and longitude to define the bounding box.

        :param request:
        :param context:
        :return:
        """

        # find the bounding box on the map
        left = min(request.rectangle.lo.long, request.rectangle.hi.long)
        right = max(request.rectangle.lo.long, request.rectangle.hi.long)
        top = max(request.rectangle.lo.lat, request.rectangle.hi.lat)
        bottom = min(request.rectangle.lo.lat, request.rectangle.hi.lat)

        self.logger.info("Request for Elements in box between ({}, {}) and ({}, {})".format(bottom, left, top, right))

        # find elements in that fall in bounding box
        elements = self.db.query(Element) \
            .filter(
            db.and_(Element.longitude >= left, Element.longitude <= right,
                    Element.latitude >= bottom, Element.latitude <= top)) \
            .all()

        for element in elements:
            activity_status = activity_status_mapper(element.status)
            location = Location(lat=element.latitude, long=element.longitude)
            asset = asset_pb2.Reply(id=element.asset.id)

            # stream reply to client
            yield element_pb2.Reply(
                id=element.id,
                status=activity_status,
                location=location,
                asset=asset,
                description=element.description
            )
