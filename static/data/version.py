import flask
from typing import *


class APIVersion:
    """
    A class to API version related information.
    """

    def __init__(self) -> None:
        """
        Initialize the API version.
        """

        self.latest_version = 'v2'

    @staticmethod
    def is_latest_api_version(query: str) -> bool:
        """
        Check if the version is the latest version.
        :param query: The version to check.
        :return: True if the version is the latest version, False otherwise.
        """

        return bool(query == APIVersion().latest_version)

    @staticmethod
    def send_invalid_api_version_response(query: str, status_code: int = 400) -> Tuple[flask.Response, int]:
        """
        Send an invalid API version response.
        :param query: The invalid API version.
        :param status_code: The status code to return.
        :return: The invalid API version response.
        """

        return flask.jsonify({'status': False, 'message': f'Invalid/Unsupported API version: "{query}"', 'tip': f'Use the latest API version: "{APIVersion().latest_version}"'}), status_code
