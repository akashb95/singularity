import logging
from log import setup_logger
import os
import settings as lighting_settings

import grpc

import lighting.element_pb2 as element_pb2
from lighting.element_pb2_grpc import ElementStub
from lighting.location_pb2 import Location, MapRect

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
    response = stub.GetElement(element_pb2.Request(id=1))
    logger.info("Element {} ({}, {}), status: {} \n{}"
                .format(response.id, response.location.lat, response.location.long,
                        element_pb2.ActivityStatus.Name(response.status),
                        response.description))

    map_rectangle = MapRect(lo=Location(long=0, lat=0), hi=Location(long=0.5, lat=0.5))
    search_response = stub.SearchElements(element_pb2.FilterByLocationRequest(rectangle=map_rectangle))

    # need to iterate over all returned replies before channel is closed
    for resp in search_response:
        logger.info("Element {} ({}, {}), status: {} \n{}"
                    .format(resp.id, resp.location.lat, resp.location.long,
                            element_pb2.ActivityStatus.Name(resp.status),
                            resp.description))

    response_all = stub.ListElements(element_pb2.Empty())
    for i, resp_list in enumerate(response_all):
        for resp in resp_list.elements:
            logger.info("Stream {} | Element {} ({}, {}), status: {} \n{}"
                        .format(i + 1, resp.id, resp.location.lat, resp.location.long,
                                element_pb2.ActivityStatus.Name(resp.status),
                                resp.description))

    # close channel.
    channel.close()
    return


if __name__ == '__main__':
    lighting_settings.load_env_vars()
    run(os.getenv("LIGHTING_COMPONENTS_PORT"))
