import logging

import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

import lighting.lib.asset_pb2 as asset_pb2
import lighting.lib.element_pb2 as element_pb2
import lighting.lib.telecell_pb2 as telecell_pb2
from dbHandler import Asset, engine
from lighting.lib.asset_pb2_grpc import AssetServicer
from log import setup_logger


class AssetHandler(AssetServicer):
    MAX_LIST_SIZE = 100

    def __init__(self):
        self.db = sessionmaker(bind=engine)()
        self.logger = setup_logger("assetHandler", logging.DEBUG)
        return

    def Get(self, request, context):
        """
        Gets a single asset by its unique ID.

        :param request:
        :param context:
        :return:
        """

        self.logger.info("Request Asset with ID of {}".format(request.id))

        asset = self.db.query(Asset).get(request.id)

        # if no asset found
        if not asset:
            return asset_pb2.Reply()

        # populate reply message
        asset_reply = self.prepare_asset_message(asset)

        return asset_reply

    def List(self, request, context):
        """
        Streams back lists of assets.

        Allows server-side definition of the largest each response stream can be. Prevents over-optimisation.

        :param request:
        :param context:
        :return:
        """

        self.logger.info("Request list of {} Assets, offset by {}".format(request.limit, request.offset))

        assets = self.db.query(Asset)

        if request.limit:
            assets = assets.limit(request.limit)

        if request.offset:
            assets = assets.offset(request.offset)

        assets = assets.all()

        replies = []

        for i, asset in enumerate(assets):
            # populate reply message
            asset_reply = self.prepare_asset_message(asset)
            replies.append(asset_reply)

            if len(replies) == self.MAX_LIST_SIZE or i == len(assets) - 1:
                reply_list = asset_pb2.ListReply()
                reply_list.assets.extend(replies)
                replies = []
                yield reply_list

    def SearchByLocation(self, request, context):
        """
        Search for assets based on a map rectangle.

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

        self.logger.info("Request for Assets in box between ({}, {}) and ({}, {})".format(bottom, left, top, right))

        # find assets in that fall in bounding box
        assets = self.db.query(Asset) \
            .filter(db.and_(Asset.longitude >= left, Asset.longitude <= right,
                            Asset.latitude >= bottom, Asset.latitude <= top)) \
            .all()

        for asset in assets:
            asset_reply = self.prepare_asset_message(asset)

            # stream reply to client
            yield asset_reply

    def Create(self, request, context):
        """
        Creates new asset.

        Does NOT create any Elements, or create associations to existing Elements.

        :param request:
        :param context:
        :return:
        """

        # don't let user define status as default zero value.
        # if user does send in 0, then let DB row store default value defined in dbHandler.
        status = request.status if request != 0 else None
        asset = Asset(status)

        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)

        message = "Created Asset {} (status: {}). Note: no elements created/associated for/to this asset." \
            .format(asset.id, asset_pb2.ActivityStatus.Name(asset.status))
        self.logger.info(message)
        context.set_details(message)

        return asset_pb2.Reply(id=asset.id, status=asset.status)

    def Update(self, request, context):
        """
        Updates existing asset.

        This method cannot be used to update any details of the child Elements that are connected to this Asset.
        For example, we cannot associate/dissociate an Element to/from the Asset this method edits from this function.

        :param request:
        :param context:
        :return:
        """

        asset = self.db.query(Asset).get(request.id)

        # if no asset found
        if not asset:
            return asset_pb2.Reply()

        if request.status:
            asset.status = request.status

        self.db.commit()

        message = "Updated {} (status: {}). Note: no elements associations modified for this asset." \
            .format(asset.id, asset_pb2.ActivityStatus.Name(asset.status))

        self.logger.info(message)

        # populate message
        asset_reply = self.prepare_asset_message(asset)
        context.set_details(message)

        return asset_reply

    def Delete(self, request, context):
        """
        Soft deletes the asset by setting its status code to the appropriate value.

        This method also cascades down to each element and TC associated to the asset.

        :param request:
        :param context:
        :return:
        """

        deleted_asset = self.db.query(Asset).get(request.id)

        # change status of affected asset
        deleted_asset.status = asset_pb2.ActivityStatus.Value("DELETED")

        deleted_elements = []
        deleted_telecells = []

        # Cascade soft deletes through chain of elements and telecells
        if deleted_asset.elements:
            for element in deleted_asset.elements:
                element.status = element_pb2.ActivityStatus.Value("DELETED")
                deleted_elements.append(element.id)

                if element.telecell:
                    element.telecell.status = telecell_pb2.ActivityStatus.Value("DELETED")
                    deleted_telecells.append(element.telecell_id)

        self.db.commit()
        self.db.refresh(deleted_asset)

        message = "Deleted Asset {}; Deleted Elements {}; Deleted Telecells {}" \
            .format(deleted_asset.id,
                    ", ".join(map(str, deleted_elements)),
                    ", ".join(map(str, deleted_telecells)))

        self.logger.info(message)

        # populate reply message
        asset_reply = asset_pb2.Reply(id=deleted_asset.id,
                                      status=deleted_asset.status)
        asset_reply.element_uids.extend(deleted_elements)
        context.set_details(message)

        return asset_reply

    def Prune(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        asset_to_be_deleted = self.db.query(Asset).get(request.id)

        if not asset_to_be_deleted:
            message = "Asset {} does not exist in system!".format(request.id)
            context.set_details(message)
            return asset_pb2.Reply()

        # get associated elements before they disappear forever...
        associated_element_ids = [element.id for element in asset_to_be_deleted.elements]

        # Going....
        self.db.delete(asset_to_be_deleted)

        # ... Going.....
        message = "Permanently deleting Asset {} and associated Elements {}." \
            .format(request.id, ", ".join(map(str, associated_element_ids)))
        self.logger.warn(message)

        # ... Gone.
        self.db.commit()

        # populate reply message
        asset = asset_pb2.Reply(id=request.id,
                                status=asset_pb2.ActivityStatus.Value("UNAVAILABLE"))
        asset.element_uids.extend(associated_element_ids)
        context.set_details(message)

        return asset

    @staticmethod
    def prepare_asset_message(asset: Asset) -> asset_pb2.Reply:
        """
        Given an Asset, prepare an Asset.Reply message which contains Asset's details.

        :param asset:
        :return:
        """

        asset_reply = asset_pb2.Reply(id=asset.id, status=asset.status)

        asset_reply.element_uids.extend([element.id for element in asset.elements])

        if asset.latitude and asset.longitude:
            asset_reply.location.long, asset_reply.location.lat = asset.longitude, asset.latitude

        else:
            asset_reply.no_location = True

        return asset_reply
