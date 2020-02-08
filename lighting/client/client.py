import logging
import os

import grpc

import lighting.lib.asset_pb2 as asset_pb2
import lighting.lib.element_pb2 as element_pb2
import lighting.lib.location_pb2 as location_pb2
import settings as lighting_settings
from lighting.lib.asset_pb2_grpc import AssetStub
from lighting.lib.element_pb2_grpc import ElementStub
from log import setup_logger

logger = setup_logger("client", logging.DEBUG)


def run(port: int):
    """
    Example function to send RPCs to the Elements server.

    :param port: Port on which to look for the server.
    :return:
    """

    # # make channel. Possible using Context Manager too.
    channel = grpc.insecure_channel('localhost:{}'.format(port))

    stub = ElementStub(channel)

    # search by id
    response = stub.Get(element_pb2.Request(id=9000))
    logger.info("Element {} ({}, {}) connected to Asset {}, status: {} \n{}"
                .format(response.id, response.location.lat, response.location.long, response.asset.id,
                        element_pb2.ActivityStatus.Name(response.status),
                        response.description))

    # search by location
    map_rectangle = location_pb2.MapRect(lo=location_pb2.Location(long=0, lat=0),
                                         hi=location_pb2.Location(long=100, lat=100))
    search_response = stub.SearchByLocation(location_pb2.FilterByLocationRequest(rectangle=map_rectangle))

    # need to iterate over all returned replies before channel is closed
    for resp in search_response:
        logger.info("Element {} ({}, {}) connected to Asset {}, status: {}\n{}"
                    .format(resp.id, resp.location.lat, resp.location.long, resp.asset.id,
                            element_pb2.ActivityStatus.Name(resp.status),
                            resp.description))

    # search list
    response_all = stub.List(element_pb2.ListRequest(limit=100, offset=10))
    for i, resp_list in enumerate(response_all):
        for resp in resp_list.elements:
            logger.info("Stream {} | Element {} ({}, {}) connected to Asset {}, status: {} \n{}"
                        .format(i + 1, resp.id, resp.location.lat, resp.location.long, resp.asset.id,
                                element_pb2.ActivityStatus.Name(resp.status),
                                resp.description))

    # Create Elements
    message = element_pb2.CreateRequest()
    elements = []
    for i in range(4):
        elements.append(element_pb2.Reply(description="{} Created by client".format(i), no_location=True))
    message.elements.extend(elements)

    response_all = stub.Create(message)
    for i, resp in enumerate(response_all.elements):
        logger.info("{} Element {} ({}, {}) connected to Asset {}, status: {} \n{}"
                    .format(i + 1, resp.id, resp.location.lat, resp.location.long, resp.asset.id,
                            element_pb2.ActivityStatus.Name(resp.status),
                            resp.description))

    # Update Element
    message = element_pb2.Reply(id=84, status=1, description="Client Updated Element")
    message.location.long, message.location.lat = 5, 5
    resp = stub.Update(message)
    logger.info("Element {} ({}, {}) connected to Asset {}, status: {} \n{}"
                .format(resp.id, resp.location.lat, resp.location.long, resp.asset.id,
                        element_pb2.ActivityStatus.Name(resp.status),
                        resp.description))

    # Soft-Delete Element
    message = element_pb2.Request(id=84)
    resp = stub.Delete(message)
    logger.info("Element {} ({}, {}) connected to Asset {}, status: {} \n{}"
                .format(resp.id, resp.location.lat, resp.location.long, resp.asset.id,
                        element_pb2.ActivityStatus.Name(resp.status),
                        resp.description))

    # Prune (permanently delete) Element
    message = element_pb2.Request(id=84)
    resp = stub.Prune(message)
    logger.info("Element {} ({}, {}) connected to Asset {}, status: {} \n{}"
                .format(resp.id, resp.location.lat, resp.location.long, resp.asset.id,
                        element_pb2.ActivityStatus.Name(resp.status),
                        resp.description))

    # Add Element to Asset
    message = element_pb2.Reply(id=489, asset_id=4)
    resp = stub.AddToAsset(message)
    logger.info("Element {} ({}, {}) connected to Asset {}, status: {} \n{}"
                .format(resp.id, resp.location.lat, resp.location.long, resp.asset.id,
                        element_pb2.ActivityStatus.Name(resp.status),
                        resp.description))

    asset_stub = AssetStub(channel)
    message = asset_pb2.Request(id=4)
    asset = asset_stub.Get(message)
    logger.info("Asset {}, with Elements {}."
                .format(asset.id, ", ".join(map(str, asset.element_uids))))

    # get Assets list
    message = asset_pb2.ListRequest(limit=150, offset=3)
    response_all = asset_stub.List(message)
    for resp_list in response_all:
        for asset in resp_list.assets:
            logger.info("Asset {}, status: {}, with Elements {}."
                        .format(asset.id, asset.status, ", ".join(map(str, asset.element_uids))))

    # create Asset
    message = asset_pb2.Reply(status=asset_pb2.ActivityStatus.Value("ACTIVE"))
    response = asset_stub.Create(message)
    logger.info("Created Asset {}, status: {}.".format(response.id, response.status))

    # Update Asset
    message = asset_pb2.Reply(id=300, status=asset_pb2.ActivityStatus.Value("INACTIVE"))
    response = asset_stub.Update(message)
    logger.info(response.message)

    # Soft-delete an asset
    message = asset_pb2.Request(id=499)
    response = asset_stub.Delete(message)
    logger.info(response.message)

    # Permanently delete an asset and associated telecells
    message = asset_pb2.Request(id=499)
    response = asset_stub.Prune(message)
    logger.info(response.message)

    # TODO #6: create stubs for Basestation, Telecell and User, and test those endpoints too.

    # close channel.
    channel.close()
    return


if __name__ == '__main__':
    lighting_settings.load_env_vars()
    run(os.getenv("LIGHTING_COMPONENTS_PORT"))
