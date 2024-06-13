import flask
from time import perf_counter
from typing import *

from static.data.version import APIVersion


# Get the latest API version
latest_api_version = APIVersion().latest_version


class OtherTools:
    """
    A class for miscellaneous tools.
    """

    class Timer:
        """
        A class for measuring the time taken by a process.
        """

        def __init__(self) -> None:
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
            :return: The formatted time taken by a process.
            """

            return float(round(data, 10))

        def get_time(self) -> float:
            """
            Get the time taken by a process.
            :return: The time taken by a process.
            """

            return OtherTools.Timer._format_time(perf_counter() - self._start_time)

        def stop_timer(self, return_time: bool = True) -> Optional[float]:
            """
            Stop the timer and get the time taken by a process.
            :param return_time: A boolean to determine if the time taken by a process should be returned.
            :return: The time taken by a process.
            """

            if return_time: return OtherTools.Timer._format_time(perf_counter() - self._start_time)
            else: return None


class APITools:
    """
    A class for API tools.
    """

    @staticmethod
    def extract_request_data(request_object: flask.Request) -> Dict[str, Dict[Any, Any]]:
        """
        Extract the request data from the current request.
        :param request_object: The current request object.
        :return: The request arguments, headers, body, and authentication.
        """

        args = request_object.args.to_dict()
        headers = dict(request_object.headers)
        body = request_object.get_json(force=True, silent=True)

        try: auth = request_object.authorization.__dict__
        except AttributeError: auth = dict()

        return {'args': args, 'headers': headers, 'body': body, 'auth': auth}

    @staticmethod
    def get_default_api_output_dict() -> Dict[str, Any]:
        """
        Get the default API output dictionary.
        :return: The default API output dictionary.
        """

        return {
            'api': {
                'status': None,
                'errorMessage': None,
                'elapsedTime': 0.0,
            },
            'response': dict(),
        }


class LimiterTools:
    """
    A class for rate limiting tools.
    """

    @staticmethod
    def gen_ratelimit_message(per_sec: Union[int, float] = None, per_min: Union[int, float] = None, per_hour: Union[int, float] = None, per_day: Union[int, float] = None) -> str:
        """
        Generate a rate limit string for any endpoint.
        :param per_sec: The number of requests allowed per second.
        :param per_min: The number of requests allowed per minute.
        :param per_hour: The number of requests allowed per hour.
        :param per_day: The number of requests allowed per day.
        :return: A rate limit string for any endpoint.
        """

        limits = [
            f'{per_sec}/second' if per_sec is not None else str(),
            f'{per_min}/minute' if per_min is not None else str(),
            f'{per_hour}/hour' if per_hour is not None else str(),
            f'{per_day}/day' if per_day is not None else str()
        ]
        return ';'.join(filter(None, limits))


class CacheTools:
    """
    A class for cache tools.
    """

    @staticmethod
    def gen_cache_key(*args, **kwargs) -> str:
        """
        Generate a cache key for the current request.
        :param args: The arguments for the current request.
        :param kwargs: The keyword arguments for the current request.
        :return: A cache key for the current request.
        """

        return str(flask.request.url)
