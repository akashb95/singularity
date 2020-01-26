import logging
from log import setup_logger

import os
from concurrent import futures
from lighting import settings as lighting_settings
from multiprocessing import cpu_count

import grpc

import lighting.element_pb2 as element_pb2
from lighting.element_pb2 import Reply, List
from lighting.element_pb2_grpc import ElementServicer, add_ElementServicer_to_server
from lighting.location_pb2 import Location
from dbHandler import elements_json

logger = setup_logger("server", logging.DEBUG)
MAX_LIST_SIZE = 2


def activity_status_mapper(activity_status: int):
    """
    Map status to defined enum types.

    :param activity_status: Integer indicating status stored in DB.
    :return:
    """

    if activity_status == 0:
        activity_status = element_pb2.UNAVAILABLE
    elif activity_status == 1:
        activity_status = element_pb2.ACTIVE
    elif activity_status == 2:
        activity_status = element_pb2.INACTIVE
    elif activity_status == 3:
        activity_status = element_pb2.UNASSOCIATED_TO_ASSET
    elif activity_status == 4:
        activity_status = element_pb2.UNASSOCIATED_TO_TC
    elif activity_status == 5:
        activity_status = element_pb2.UNASSOCIATED_TO_ASSET_AND_TC
    elif activity_status == 15:
        activity_status = element_pb2.DELETED

    return activity_status


class ElementHandler(ElementServicer):

    def GetElement(self, request, context):
        """
        Gets a single element by its unique id.

        :param request:
        :param context:
        :return:
        """

        element = elements_json.by_id(request.id)

        # if no element found
        if not element:
            return Reply()

        # if any of these fields empty, then gRPC will return the default value (0 for int, empty string for str, etc.)
        uid = element.get('id', -1)  # make default value -1 because id may well be zer-indexed.
        activity_status = activity_status_mapper(element['status'])

        location = Location(lat=element.get('lat'), long=element.get('long'))
        description = element.get('description')

        return Reply(
            id=uid,
            status=activity_status,
            location=location,
            description=description
        )

    def ListElements(self, request, context):
        """
        Streams back lists of elements.

        Allows server-side definition of the largest each response stream can be. Prevents over-optimisation.

        :param request:
        :param context:
        :return:
        """

        # get elements
        elements = elements_json.get_all()
        replies = []

        for i, element in enumerate(elements):
            replies.append(
                Reply(id=element['id'],
                      status=activity_status_mapper(element['status']),
                      location=Location(lat=element.get('lat'), long=element.get('long')),
                      description=element.get('description'))
            )

            if len(replies) == MAX_LIST_SIZE or i == len(elements) - 1:
                reply_list = element_pb2.List()
                reply_list.elements.extend(replies)
                replies = []
                yield reply_list

    def SearchElements(self, request, context):
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

        # find elements in that fall in bounding box
        elements = elements_json.get_all()
        for element in elements:
            lat = element.get('lat', 0)
            long = element.get('long', 0)

            if top >= lat >= bottom and right >= long >= left:
                uid = element.get('id', -1)
                activity_status = activity_status_mapper(element.get('status', 0))
                location = Location(lat=element.get('lat'), long=element.get('long'))
                description = element.get('description')

                # stream reply to client
                yield Reply(
                    id=uid,
                    status=activity_status,
                    location=location,
                    description=description
                )


def serve(port: int):
    """
    Start up server, multithreaded to the number of CPUs that the hosting machine has.

    :param port: Port on which to serve up this service
    :return:
    """

    num_cpus = cpu_count()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=num_cpus))
    add_ElementServicer_to_server(ElementHandler(), server)
    server.add_insecure_port('[::]:{}'.format(port))
    logger.debug("Listening on port {}".format(port))

    server.start()
    server.wait_for_termination()
    return


if __name__ == '__main__':
    lighting_settings.load_env_vars()
    serve(os.getenv("LIGHTING_COMPONENTS_PORT"))
