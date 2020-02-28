import logging

import grpc
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

import lighting.lib.element_pb2 as element_pb2
from dbHandler import Element, Asset, engine
from lighting.lib.element_pb2_grpc import ElementServicer
from lighting.server.handler.asset import AssetHandler
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
            context.set_details("Element {} not found in system.".format(request.id))
            return element_pb2.Reply()

        # get associated asset, and the elements that asset is connected to
        element_reply = self.prepare_element_message(element)

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
            element_reply = self.prepare_element_message(element)

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
        assets_subquery = self.db.query(Asset).filter(
            db.and_(Asset.longitude >= left, Asset.longitude <= right,
                    Asset.latitude >= bottom, Asset.latitude <= top)
        ).subquery()
        elements = self.db.query(Element).join(assets_subquery, assets_subquery.c.id == Element.asset_id).all()

        for element in elements:
            element_reply = self.prepare_element_message(element)

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
            new_element = Element(asset=new_asset, description=element.description)

            # don't let the user set status to 0, as this is the default zero value
            if element.status != 0:
                new_element.status = element.status
            else:
                new_element.status = element_pb2.ActivityStatus.Value("INACTIVE")

            new_elements.append(new_element)

        # add new asset and new elements to session, and commit to DB.
        new_db_entries = [new_asset, *new_elements]
        self.db.add_all(new_db_entries)
        self.db.commit()
        for entry in new_db_entries:
            self.db.refresh(entry)

        element_ids = ", ".join(map(str, [element.id for element in new_elements]))
        message = "Created Asset {} and Elements {}".format(new_asset.id, element_ids)
        self.logger.info(message)
        context.set_details(message)

        # populate reply message - asset will be the same for all new elements created by this RPC
        asset_reply = AssetHandler.prepare_asset_message(new_elements[0].asset)

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
            return element_pb2.Reply(id=request.id)

        # expecting either new asset ID (int) or an entire asset message.
        if request.asset_id != 0:

            # check asset exists
            asset = self.db.query(Asset).get(request.asset_id)

            if asset is None:
                message = "Request to update Element {}'s Asset failed: " \
                          "Asset does not appear to exist!".format(request.asset_id)

                self.logger.warn(message)

                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(message)
                return element_pb2.Reply(id=request.id)

            element.asset_id = request.asset_id

        elif request.asset and request.asset.id != 0:

            # check asset exists
            asset = self.db.query(Asset).get(request.asset.id)

            if asset is None:
                message = "Request to update Element {}'s Asset failed: " \
                          "Asset does not appear to exist!".format(request.asset.id)

                self.logger.warn(message)

                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(message)
                return element_pb2.Reply(id=request.id)

            element.asset = request.asset

        # update the other details where required.
        if request.status:
            element.status = request.status

        if request.description:
            element.description = request.description

        self.db.commit()

        # prepare element reply
        element_reply = self.prepare_element_message(element)

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
            context.set_details("Element {} does not exist!".format(request.id))
            return element_pb2.Reply(id=request.id)

        element.status = element_pb2.ActivityStatus.Value("DELETED")

        self.db.commit()

        # prepare asset message
        element_reply = self.prepare_element_message(element)

        message = "Set status of Element {} to DELETED (soft-deletion).".format(element.id)
        self.logger.info(message)
        context.set_details(message)

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
            context.set_details("Element {} does not exist!".format(request.id))
            return element_pb2.Reply(id=request.id)

        message = "Deleted Element {} (permanently).".format(element.id)

        self.db.delete(element)
        self.db.commit()

        self.logger.info(message)
        context.set_details(message)

        return element_pb2.Reply(id=request.id)

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
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Element {} does not exist!".format(request.id))
            return element_pb2.Reply(id=request.id, asset_id=request.asset_id)

        # get asset from DB if exists, or send back an error
        asset = self.db.query(Asset).get(request.asset_id)

        if not asset:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Asset {} does not exist!".format(request.asset_id))
            return element_pb2.Reply(id=request.id, asset_id=request.asset_id)

        # associate element to asset and commit changes to DB
        old_element_asset_id = element.asset.id  # for logging
        element.asset = asset
        self.db.commit()

        message = "Added Element {} to Asset {}, dissociated from Asset {}" \
            .format(element.id, element.asset.id, old_element_asset_id)
        self.logger.info(message)
        context.set_details(message)

        # prepare element message
        element_reply = self.prepare_element_message(element)

        return element_reply

    @staticmethod
    def prepare_element_message(element: Element) -> element_pb2.Reply:
        asset_reply = AssetHandler.prepare_asset_message(element.asset)
        element_reply = element_pb2.Reply(id=element.id,
                                          status=element.status,
                                          description=element.description,
                                          asset=asset_reply)

        return element_reply
