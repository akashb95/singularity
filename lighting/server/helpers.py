import lighting.element_pb2 as element_pb2


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
