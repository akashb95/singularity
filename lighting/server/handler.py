import lighting.element_pb2 as element_pb2
from lighting.element_pb2_grpc import ElementServicer
from lighting.location_pb2 import Location
from dbHandler import elements_json
from lighting.server.helpers import activity_status_mapper


class ElementHandler(ElementServicer):
    MAX_LIST_SIZE = 2

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
            return element_pb2.Reply(id=-1)

        # if any of these fields empty, then gRPC will return the default value (0 for int, empty string for str, etc.)
        uid = element.get('id', -1)  # make default value -1 because id may well be zer-indexed.
        activity_status = activity_status_mapper(element['status'])

        location = Location(lat=element.get('lat'), long=element.get('long'))
        description = element.get('description')

        return element_pb2.Reply(
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
                element_pb2.Reply(id=element['id'],
                                  status=activity_status_mapper(element['status']),
                                  location=Location(lat=element.get('lat'), long=element.get('long')),
                                  description=element.get('description'))
            )

            if len(replies) == self.MAX_LIST_SIZE or i == len(elements) - 1:
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
                yield element_pb2.Reply(
                    id=uid,
                    status=activity_status,
                    location=location,
                    description=description
                )
