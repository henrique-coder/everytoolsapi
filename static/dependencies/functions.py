import flask
from collections import defaultdict
from time import time, perf_counter
from typing import *

from static.dependencies.exceptions import Exceptions


app = flask.current_app


class WebErrorHandler:
    pass

class IPRequestLimits:
    ip_requests = defaultdict(list)
    ban_duration = 60

    @staticmethod
    def clean_old_requests(ip_address: str) -> None:
        """
        Remove requests that are older than the ban duration.
        :param ip_address: The IP address of the request.
        """

        current_time = time()
        IPRequestLimits.ip_requests[ip_address] = [t for t in IPRequestLimits.ip_requests[ip_address] if current_time - t <= IPRequestLimits.ban_duration]

    @staticmethod
    def check_request_limits(ip_address: str, limits: dict) -> bool:
        """
        Check if the request limits are exceeded for the given IP address.
        :param ip_address: The IP address of the request.
        :param limits: The rate limits for the different time periods.
        """

        current_time = time()
        IPRequestLimits.clean_old_requests(ip_address)

        if limits.get('one_every', 0) > 0:
            last_request_time = IPRequestLimits.ip_requests[ip_address][-1] if IPRequestLimits.ip_requests[ip_address] else 0

            if current_time - last_request_time < limits['one_every']:
                return False

        for period, limit in [('minute', 'max_per_minute'), ('hour', 'max_per_hour'), ('day', 'max_per_day')]:
            if limits.get(limit, 0) > 0:
                period_requests = [t for t in IPRequestLimits.ip_requests[ip_address] if (current_time - t < 3600 and period == 'hour') or (current_time - t < 60 and period == 'minute') or True]

                if len(period_requests) >= limits[limit]:
                    return False

        IPRequestLimits.ip_requests[ip_address].append(current_time)
        return True

class RateLimitFunctions:
    @staticmethod
    def gen_ratelimit_dict(data: Optional[Tuple[int, int, int, int]] = (0, 300, 10000, 100000)) -> Dict[str, int]:
        """
        Generate a dictionary with the rate limits for the different time periods.
        :param data: A tuple with the rate limits for the different time periods. The tuple should have the following format: (one_every, max_per_minute, max_per_hour, max_per_day). If no data is provided, the default values will be used.
        """

        data = (0, 60, 3600, 86400) if not data else data
        return {'one_every': data[0], 'max_per_minute': data[1], 'max_per_hour': data[2], 'max_per_day': data[3]}

class APITools:
    class Timer:
        """
        A class for measuring the time taken by a process.
        """

        def __init__(self):
            """
            Initialize the Timer class.
            """

            self._start_time = perf_counter()
            self._end_time = 0

        @staticmethod
        def _format_time(data: float) -> float:
            """
            Format the time taken by a process.
            :param data: The time taken by a process.
            """

            return float(round(data, 3))

        def get_time(self) -> float:
            """
            Get the time taken by a process.
            """

            return APITools.Timer._format_time(perf_counter() - self._start_time)

        def stop_timer(self, return_time: bool = True) -> Optional[float]:
            """
            Stop the timer and get the time taken by a process.
            :param return_time: A boolean to determine if the time taken by a process should be returned.
            """

            if return_time: return APITools.Timer._format_time(perf_counter() - self._start_time)
            else: return None

    @staticmethod
    def check_main_request(remote_ipv4_addr: str, rate_limits: Optional[Tuple[int, int, int, int]], query_version: Optional[str] = None, latest_api_version:Optional[str] = None) -> None:
        """
        Check the main request for the API.
        :param remote_ipv4_addr: The IPv4 address of the request.
        :param rate_limits: The rate limits for the different time periods. The tuple should have the following format: (one_every, max_per_minute, max_per_hour, max_per_day).
        :param query_version: The version of the API that is being queried.
        :param latest_api_version: The latest version of the API.
        """

        if not IPRequestLimits.check_request_limits(remote_ipv4_addr, RateLimitFunctions.gen_ratelimit_dict(rate_limits)):
            return flask.abort(429)

        if query_version and latest_api_version:
            if query_version != latest_api_version:
                return flask.abort(404)

        return None

    @staticmethod
    def endpoint_api_in_maintenance(error_code: int = 503) -> None:
        """
        Return an error response for the API when it is in maintenance.
        :param error_code: The error code to return.
        """

        return flask.abort(error_code)

    @staticmethod
    def gen_api_status_response_dict(has_existed: bool, query_version: str = None, latest_version: str = None) -> dict:
        """
        Generate a dictionary with the API response.
        :param has_existed: A boolean to determine if the API version is existing.
        :param query_version: The version of the API that is being queried.
        :param latest_version: The latest version of the API.
        """

        if has_existed:
            if query_version == latest_version:
                return {'isLatest': True, 'hasExisted': True, 'latestVersion': latest_version, 'message': Exceptions.USING_LATEST_API_VERSION.message}
            else:
                return {'isLatest': False, 'hasExisted': True, 'latestVersion': latest_version, 'message': Exceptions.USING_OUTDATED_API_VERSION.message}
        else:
            return {'isLatest': False, 'hasExisted': False, 'latestVersion': latest_version, 'message': Exceptions.USING_INVALID_API_VERSION.message}

    @staticmethod
    def gen_api_output_dict(elapsed_time: float, data: dict = None) -> dict:
        """
        Generate a dictionary with the API output.
        :param elapsed_time: The time taken by the process.
        :param data: The data generated by the process.
        """

        output_data = {'api': {'success': data['success'], 'elapsedTime': elapsed_time, 'errorMessage': data['errorMessage']}, 'response': data['response']}
        return output_data

    @staticmethod
    def set_none_if_empty(data: Any) -> Optional[Any]:
        """
        Set a value to None if it is empty.
        :param data: Any value to check.
        """

        try:
            if isinstance(data, str) and not data.strip():
                return None
            elif isinstance(data, list):
                stripped_data = [item.strip() if isinstance(item, str) else item for item in data]
                if all(item is None for item in stripped_data):
                    return None
                elif all(item == str() for item in stripped_data):
                    return None
                else:
                    return stripped_data
            elif isinstance(data, dict):
                stripped_dict = {}
                for key, value in data.items():
                    if isinstance(key, str):
                        stripped_key = key.strip()
                        if stripped_key == str():
                            continue
                    else:
                        stripped_key = key
                    if isinstance(value, str):
                        stripped_value = value.strip()
                        if stripped_value == str():
                            stripped_value = None
                    else:
                        stripped_value = value
                    stripped_dict[stripped_key] = stripped_value
                if not stripped_dict:
                    return None
                else:
                    return stripped_dict
            elif isinstance(data, (tuple, set)):
                if not data:
                    return None
                else:
                    return data
            elif isinstance(data, bool) and not data:
                return None
            elif data is None:
                return None
            else:
                return data
        except AttributeError:
            return None

    @staticmethod
    def remove_keys_from_dict(data: dict, keys: List[str]) -> dict:
        """
        Remove keys from a dictionary.
        :param data: The dictionary to remove keys from.
        :param keys: The keys to remove from the dictionary.
        """

        for key in keys: data.pop(key, None)
        return data

    @staticmethod
    def get_default_output_dict() -> dict:
        """
        Get the default output dictionary. (success: False, errorMessage: str(), response: dict())
        """

        return {'success': False, 'errorMessage': str(), 'response': dict()}
