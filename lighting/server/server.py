import logging
import os
from concurrent import futures
from multiprocessing import cpu_count

import grpc

import settings as lighting_settings
from lighting.lib.asset_pb2_grpc import add_AssetServicer_to_server
from lighting.lib.element_pb2_grpc import add_ElementServicer_to_server
from lighting.server.handler import ElementHandler, AssetHandler
from log import setup_logger

logger = setup_logger("server", logging.DEBUG)


def serve(port: int):
    """
    Start up server, multithreaded to the number of CPUs that the hosting machine has.

    :param port: Port on which to serve up this service
    :return:
    """

    num_cpus = cpu_count()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=num_cpus))
    add_ElementServicer_to_server(ElementHandler(), server)
    add_AssetServicer_to_server(AssetHandler(), server)
    server.add_insecure_port('[::]:{}'.format(port))
    logger.debug("Listening on port {}".format(port))

    server.start()
    server.wait_for_termination()
    return


if __name__ == '__main__':
    lighting_settings.load_env_vars()
    serve(os.getenv("LIGHTING_COMPONENTS_PORT"))
