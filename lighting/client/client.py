import logging
from log import setup_logger
import os
import settings as lighting_settings

import grpc

import lighting.lib.element_pb2 as element_pb2
import lighting.lib.location_pb2 as location_pb2
from lighting.lib.element_pb2_grpc import ElementStub

logger = setup_logger("client", logging.DEBUG)


def run(port: int):
    """
    Example function to send RPCs to the Elements server.

    :param port: Port on which to look for the server.
    :return:
    """

    # make channel. Possible using Context Manager too.
    channel = grpc.insecure_channel('localhost:{}'.format(port))

    stub = ElementStub(channel)

    # search by id
    response = stub.Get(element_pb2.Request(id=9))
    logger.info("Element {} ({}, {}) connected to Asset {}, status: {} \n{}"
                .format(response.id, response.location.lat, response.location.long, response.asset.id,
                        element_pb2.ActivityStatus.Name(response.status),
                        response.description))

    # search by location
    map_rectangle = location_pb2.MapRect(lo=location_pb2.Location(long=0, lat=0),
                                         hi=location_pb2.Location(long=100, lat=10))
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

    # close channel.
    channel.close()

    # TODO #6: create channels with stubs for Basestation, Asset, Telecell and User, and test those endpoints too.

    return


if __name__ == '__main__':
    lighting_settings.load_env_vars()
    run(os.getenv("LIGHTING_COMPONENTS_PORT"))
