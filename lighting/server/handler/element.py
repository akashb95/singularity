import logging

import grpc
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

import lighting.lib.asset_pb2 as asset_pb2
import lighting.lib.element_pb2 as element_pb2
from dbHandler import Element, Asset, engine
from lighting.lib.element_pb2_grpc import ElementServicer
from log import setup_logger


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

        # get associated asset, and the elements that asset is connected to
        asset_reply = self._prepare_asset_message(element)

        element_reply = element_pb2.Reply(id=element.id, status=element.status,
                                          asset=asset_reply, description=element.description)
        element_reply = self._set_location_oneof(element, element_reply)

        return element_reply

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
            asset_reply = self._prepare_asset_message(element)
            element_reply = element_pb2.Reply(
                id=element.id,
                status=element.status,
                asset=asset_reply,
                description=element.description)
            self._set_location_oneof(element, element_reply)

            replies.append(element_reply)

            if len(replies) == self.MAX_LIST_SIZE or i == len(elements) - 1:
                # populate outgoing message
                reply_list = element_pb2.ListReply()
                reply_list.elements.extend(replies)

                # reset list for next batch of messages that'll go in the next stream
                replies = []

                # stream
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
            asset_reply = self._prepare_asset_message(element)
            element_reply = element_pb2.Reply(
                id=element.id,
                status=element.status,
                asset=asset_reply,
                description=element.description
            )
            element_reply = self._set_location_oneof(element, element_reply)

            # stream reply to client
            yield element_reply

    def Create(self, request, context):
        """
        Creates a new Asset and adds the new Elements to it.

        This is essentially the 'asset import' functionality.

        :param request:
        :param context:
        :return:
        """

        # create new asset
        new_asset = Asset()
        new_elements = []

        for element in request.elements:
            # if location not specified, then they'll be stored as NULL values in DB.
            if element.no_location:
                new_element = Element(asset=new_asset,
                                      description=element.description)
            else:
                new_element = Element(asset=new_asset,
                                      description=element.description,
                                      latitude=element.location.latitude,
                                      longitude=element.location.longitude)

            # don't let the user set status to 0, as this is the default zero value
            if request.status != 0:
                new_element.status = request.status
            else:
                new_element.status = 1

            new_elements.append(new_element)

        # add new asset and new elements to session, and commit to DB.
        new_db_entries = [new_asset, *new_elements]
        self.db.add(new_db_entries)
        self.db.commit()
        for entry in new_db_entries:
            self.db.refresh(entry)

        # populate reply message - asset will be the same for all new elements created by this RPC
        asset_reply = self._prepare_asset_message(new_elements[0])

        # prepare empty message to send back list of elements created.
        elements_reply = element_pb2.ListReply()

        # get details of each element and put into the appropriate message.
        element_replies = []

        for element in new_elements:
            # populate element message
            element_reply = element_pb2.Reply(id=element.id,
                                              status=element.status,
                                              description=element.description,
                                              asset=asset_reply)
            element_reply = self._set_location_oneof(element, element_reply)

            # save to list of elements that will be sent out finally
            element_replies.append(element_reply)

        # add individual elements to the reply message
        elements_reply.elements.extend(element_replies)

        return elements_reply

    def Update(self, request, context):

        element = self.db.query(Element).get(request.id)

        # do validation on those fields first that could raise an error - minimise unnecessary steps
        # if this element isn't in the DB, return helpful message to user.
        if not element:
            message = "Request to update Element {} failed: Element does not appear to exist!".format(request.id)
            self.logger.warn(message)
            return element_pb2.Reply(id=request.id, message=message)

        # expecting either new asset ID (int) or an entire asset message.
        if request.asset_id:

            # check asset exists
            asset = self.db(Asset).get(request.asset_id)

            if asset is None:
                message = "Request to update Element {}'s Asset failed: " \
                          "Asset does not appear to exist!".format(request.asset_id)
                self.logger.warn(message)
                return element_pb2.Reply(id=request.id, message=message)

            element.asset_id = request.asset_id

        elif request.asset:

            # check asset exists
            asset = self.db(Asset).get(request.asset.id)

            if asset is None:
                message = "Request to update Element {}'s Asset failed: " \
                          "Asset does not appear to exist!".format(request.asset.id)
                self.logger.warn(message)
                return element_pb2.Reply(id=request.id, message=message)

            element.asset = request.asset

        # update the other details where required.
        if request.status:
            element.status = request.status

        if request.description:
            element.description = request.description

        if not request.location.no_location:
            element.longitude = request.location.longitude
            element.latitude = request.location.latitude

        self.db.commit()

        # prepare asset message
        asset_reply = self._prepare_asset_message(element)

        # prepare element reply
        element_reply = element_pb2.Reply(id=request.id,
                                          status=element.status,
                                          description=element.description,
                                          asset=asset_reply)
        element_reply = self._set_location_oneof(element, element_reply)

        return element_reply

    def Delete(self, request, context):
        """
        Soft-deletes an element by its ID from the system by setting its status field to the appropriate value.

        :param request:
        :param context:
        :return:
        """

        element = self.db.query(Element).get(request.id)

        if not element:
            context.set_code(400)
            context.set_details("Element {} does not exist!".format(request.id))
            return element_pb2.Reply(id=request.id, no_location=True)

        element.status = element_pb2.ActivityStatus.Value("DELETED")

        self.db.commit()

        # prepare asset message
        asset_reply = self._prepare_asset_message(element)

        # prepare element message
        element_reply = element_pb2.Reply(id=request.id, status=element.status,
                                          description=element.description, asset=asset_reply)
        element_reply = self._set_location_oneof(element, element_reply)

        return element_reply

    def Prune(self, request, context):
        """
        Permanently deletes an element by its ID from the system.

        :param request:
        :param context:
        :return:
        """

        element = self.db.query(Element).get(request.id)

        if not element:
            context.set_code(400)
            context.set_details("Element {} does not exist!".format(request.id))
            return element_pb2.Reply(id=request.id, no_location=True)

        self.db.delete(element)
        self.db.commit()

        return element_pb2.Reply(id=request.id, no_location=True)

    def AddToAsset(self, request, context):
        """
        Adds Element by ID to an Asset by ID.

        Expects the lighting.element.Reply.asset_id field to be populated as this identifies the Asset this Element will
        become associated to.

        :param request:
        :param context:
        :return:
        """

        # get element from DB if exists, or send back an error.
        element = self.db.query(Element).get(request.id)

        if not element:
            context.set_code(400)
            context.set_details("Element {} does not exist!".format(request.id))
            return element_pb2.Reply(id=request.id, no_location=True, asset_id=request.asset_id)

        # get asset from DB if exists, or send back an error
        asset = self.db.query(Asset).get(request.asset_id)

        if not asset:
            context.set_code(400)
            context.set_details("Asset {} does not exist!".format(request.asset_id))
            return element_pb2.Reply(id=request.id, no_location=True, asset_id=request.asset_id)

        # associate element to asset and commit changes to DB
        element.asset = asset
        self.db.commit()

        # prepare asset message
        asset_reply = self._prepare_asset_message(element)

        # prepare element message
        element_reply = element_pb2.Reply(id=element.id, status=element.status,
                                          description=element.description,
                                          asset=asset_reply)
        element_reply = self._set_location_oneof(element, element_reply)

        return element_reply

    @staticmethod
    def _set_location_oneof(element: Element, element_reply: element_pb2.Reply):
        """
        Checks if the element has non-null longitude and latitude, and sets Element.Reply.location_oneof accordingly.

        If both lat and long are non-null, then obviously location exists, and so the coordinates set on Reply message.
        Otherwise, set no_location field in Reply to be True.

        :param element: {dbHandler.Element} Element returned by DB query.
        :param element_reply: Reply message
        :return:
        """

        if element.longitude is not None and element.latitude is not None:
            element_reply.location.long, element_reply.location.lat = element.longitude, element.latitude

        else:
            element_reply.no_location = True

        return element_reply

    @staticmethod
    def _prepare_asset_message(element: Element):
        """
        Given an Element, prepare an Asset.Reply message which contains Asset's details.

        :param element:
        :return:
        """

        asset_reply = asset_pb2.Reply(id=element.asset.id, status=element.asset.status)
        asset_reply.element_uids.extend([element.id for element in element.asset.elements])

        return asset_reply
