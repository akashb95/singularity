"""
Temporary solution, in reality, we'd use some sort of DB.
Get entries from mock JSON data in data/elements.json.
"""

import json
import os

# assuming that the caller script is being run from the project root dir.
PATH_TO_JSON = os.path.join("..", "data", "elements.json")


def open_data_file():
    """
    Reads JSON data into a Python dictionary.
    :return:
    """

    with open(PATH_TO_JSON, "r") as data_file:
        elements = json.load(data_file)

    return elements


def get_all():
    """
    :return:
    """

    return open_data_file()


def by_id(uid: int):
    """
    :param uid: Element unique identifier
    :return: None if no entry found, and element details if entry found.
    """

    elements = open_data_file()
    for element in elements:
        if element["id"] == uid:
            return element

    return None


def by_active_status(active_status: bool):
    """

    :param active_status:
    :return:
    """

    elements = open_data_file()
    results = []

    for element in elements:
        if element["active"] == active_status:
            results.append(element)

    return results
