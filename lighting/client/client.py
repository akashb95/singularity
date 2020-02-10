import logging
import os

import grpc

import lighting.lib.asset_pb2 as asset_pb2
import lighting.lib.basestation_pb2 as bs_pb2
import lighting.lib.element_pb2 as element_pb2
import lighting.lib.location_pb2 as location_pb2
import lighting.lib.user_pb2 as user_pb2
import settings as lighting_settings
from lighting.lib.asset_pb2_grpc import AssetStub
from lighting.lib.basestation_pb2_grpc import BasestationStub
from lighting.lib.element_pb2_grpc import ElementStub
from lighting.lib.telecell_pb2_grpc import TelecellStub
from lighting.lib.user_pb2_grpc import UserStub
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

    # Asset stub
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
    message = asset_pb2.Reply(id=301, status=asset_pb2.ActivityStatus.Value("INACTIVE"))
    response, call = asset_stub.Update.with_call(message)
    logger.info(call.details())

    # Soft-delete an asset
    message = asset_pb2.Request(id=499)
    response, call = asset_stub.Delete.with_call(message)
    logger.info(call.details())

    # Permanently delete an asset and associated telecells
    message = asset_pb2.Request(id=499)
    response, call = asset_stub.Prune.with_call(message)
    logger.info(call.details())

    # User stub
    user_stub = UserStub(channel)

    # Get a user
    message = user_pb2.Request(id=1)
    user = user_stub.Get(message)
    logger.info("User {} (ID: {}) has role {}"
                .format(user.username, user.id, user_pb2.Role.Name(user.role)))

    # Create User
    message = user_pb2.Reply(username="telensa-ab", hashed_pass="potato", role=user_pb2.Role.Value("ADMIN"))
    user = user_stub.Create(message)
    logger.info("User {} (ID: {}) has role {}"
                .format(user.username, user.id, user_pb2.Role.Name(user.role)))

    # Update User record
    message = user_pb2.Reply(id=1, username="telensa-nu", role=6)
    user = user_stub.Update(message)
    logger.info("User {} (ID: {}) has role {}"
                .format(user.username, user.id, user_pb2.Role.Name(user.role)))

    # Delete User record
    message = user_pb2.Request(username="telensa-ab")
    user = user_stub.Delete(message)
    logger.info("Deleted || User {} (ID: {}) has role {}"
                .format(user.username, user.id, user_pb2.Role.Name(user.role)))

    # Basestation stub
    bs_stub = BasestationStub(channel)

    # Get a BS
    message = bs_pb2.Request(id=3)
    bs = bs_stub.Get(message)
    logger.info("Basestation {} (UUID: {}) is at ({}, {}) and has status {}."
                .format(bs.id, bs.uuid, bs.location.long, bs.location.lat, bs_pb2.ActivityStatus.Name(bs.status)))

    # Create BS
    location = location_pb2.Location(lat=12, long=123)
    message = bs_pb2.Reply(uuid=12346, location=location, version=4)
    bs = bs_stub.Create(message)
    logger.info("Created Basestation {} (UUID: {}) is at ({}, {}) and has status {}."
                .format(bs.id, bs.uuid, bs.location.long, bs.location.lat, bs_pb2.ActivityStatus.Name(bs.status)))

    # Search BS by location
    map_rectangle = location_pb2.MapRect(lo=location_pb2.Location(long=0, lat=0),
                                         hi=location_pb2.Location(long=100, lat=129))
    search_response = bs_stub.SearchByLocation(location_pb2.FilterByLocationRequest(rectangle=map_rectangle))

    # need to iterate over all returned replies before channel is closed
    for bs in search_response:
        logger.info("Basestation {} (UUID: {}) is at ({}, {}), and has status: {}\n"
                    .format(bs.id, bs.uuid, bs.location.long, bs.location.lat, bs.status))

    # List all basestations
    response_all = bs_stub.List(bs_pb2.ListRequest(limit=100, offset=1))
    for i, resp_list in enumerate(response_all):
        for resp in resp_list.basestations:
            logger.info("Stream {} | Basestation {} (UUID: {}) located at: ({}, {}) has status {}."
                        .format(i + 1, resp.id, resp.uuid, resp.location.lat, resp.location.long,
                                bs_pb2.ActivityStatus.Name(resp.status)))

    # Update a BS
    message = bs_pb2.Reply(uuid=12345, status=bs_pb2.ActivityStatus.Value("ACTIVE"), no_location=True)
    bs = bs_stub.Update(message)
    logger.info("Basestation {} (UUID: {}) located at: ({}, {}) has status {}."
                .format(bs.id, bs.uuid, bs.location.long, bs.location.lat, bs_pb2.ActivityStatus.Name(bs.status)))

    # Delete BS
    message = bs_pb2.Request(uuid=12345)
    bs = bs_stub.Delete(message)
    logger.info("Basestation {} (UUID: {}) located at ({}, {}) has status {}."
                .format(bs.id, bs.uuid, bs.location.long, bs.location.lat, bs_pb2.ActivityStatus.Name(bs.status)))

    # Prune (permanently delete) BS
    message = bs_pb2.Request(uuid=12345)
    bs = bs_stub.Prune(message)
    logger.info("Basestation {} (UUID: {}) located at ({}, {}) has status {}."
                .format(bs.id, bs.uuid, bs.location.long, bs.location.lat, bs_pb2.ActivityStatus.Name(bs.status)))

    # Telecell stub
    tc_stub = TelecellStub(channel)
    # TODO #10: Test TelecellHandler

    # close channel.
    channel.close()
    return


if __name__ == '__main__':
    lighting_settings.load_env_vars()
    run(os.getenv("LIGHTING_COMPONENTS_PORT"))
