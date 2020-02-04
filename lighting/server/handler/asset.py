import logging

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

        # get UIDs of connected elements
        element_uids = [element.id for element in asset.elements]

        # populate reply message
        asset = asset_pb2.Reply(id=asset.id, status=asset.status)
        asset.element_uids.extend(element_uids)

        return asset

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
            # get UIDs of connected elements
            element_uids = [element.id for element in asset.elements]

            # populate reply message
            replies.append(asset_pb2.Reply(id=asset.id, status=asset.status))
            replies.extend(element_uids)

            if len(replies) == self.MAX_LIST_SIZE or i == len(assets) - 1:
                reply_list = asset_pb2.ListReply()
                reply_list.elements.extend(replies)
                replies = []
                yield reply_list

    def Create(self, request, context):
        """
        Creates new asset.

        :param request:
        :param context:
        :return:
        """

        asset = Asset(request.status)

        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)

        return asset_pb2.Reply(id=asset.id, status=asset.status)

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
            .format(deleted_asset.id, ", ".join(deleted_elements), ", ".join(deleted_telecells))

        self.logger.info(message)

        # populate reply message
        asset = asset_pb2.Reply(id=deleted_asset.id,
                                status=deleted_asset.status,
                                message=message)
        asset.element_uids.extend(deleted_elements)

        return asset

    def Prune(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        asset_to_be_deleted = self.db.query(Asset).get(Asset.id == request.id)

        # just for logging
        associated_element_ids = [element.id for element in asset_to_be_deleted.elements]

        # Going....
        self.db.delete(asset_to_be_deleted)

        # ... Going.....
        message = "Permanently deleting Asset {} and associated Elements {}." \
            .format(request.id, ", ".join(associated_element_ids))
        self.logger.warn(message)

        # ... Gone.
        self.db.commit()

        # populate reply message
        asset = asset_pb2.Reply(id=request.id,
                                status=asset_pb2.ActivityStatus.Value("UNAVAILABLE"),
                                message=message)
        asset.element_uids.extend(associated_element_ids)

        return asset
