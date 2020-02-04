import logging
from log import setup_logger

import lighting.lib.element_pb2 as element_pb2
from lighting.lib.asset_pb2_grpc import AssetServicer
import lighting.lib.asset_pb2 as asset_pb2
import lighting.lib.telecell_pb2 as telecell_pb2

from dbHandler import Asset, engine
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker


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

        return asset_pb2.Reply(id=asset.id)

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

        for i, element in enumerate(assets):
            replies.append(asset_pb2.Reply(id=element.id))

            if len(replies) == self.MAX_LIST_SIZE or i == len(assets) - 1:
                reply_list = element_pb2.ListReply()
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

        asset = Asset()

        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)

        return asset_pb2.Reply(asset.id)

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

        return asset_pb2.Reply(id=deleted_asset.id,
                               status=deleted_asset.status,
                               message=message)

    def Prune(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """

        self.db.query(Asset).filter(Asset.id == request.id).delete()
        self.db.commit()

        return
