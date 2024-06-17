from flask import request, Request
from time import perf_counter
from datetime import timedelta, datetime, UTC
from typing import *

from static.data.version import APIVersion


# Get the latest API version
latest_api_version = APIVersion().latest_version


class APITools:
    """
    A class for API tools.
    """

    @staticmethod
    def extract_request_data(request_object: Request) -> Dict[str, Dict[Any, Any]]:
        """
        Extract the request data from the current request.
        :param request_object: The current request object.
        :return: The request arguments, headers, body, and authentication.
        """

        route = str(request_object.path)
        remote_addr = request_object.remote_addr
        args = request_object.args.to_dict()
        headers = dict(request_object.headers)
        body = request_object.get_json(force=True, silent=True)

        try: auth = request_object.authorization.__dict__
        except AttributeError: auth = dict()

        return {'pathRoute': route, 'ipAddress': remote_addr, 'args': args, 'headers': headers, 'body': body, 'auth': auth}

    @staticmethod
    def get_default_api_output_dict() -> Dict[str, Any]:
        """
        Get the default API output dictionary.
        :return: The default API output dictionary.
        """

        return {
            'api': {
                'status': False,
                'errorMessage': None,
                'elapsedTime': None,
                'version': latest_api_version,
            },
            'response': dict(),
        }

    class Timer:
        """
        A class for measuring the time taken by a process.
        """

        def __init__(self, start: bool = True) -> None:
            """
            Initialize the Timer class.
            :param start: Whether to start the timer immediately.
            """

            self.start_time = None
            self.end_time = None
            self._start_perf_counter = None
            self._stop_perf_counter = None

            if start: self.start()

        def start(self) -> None:
            """
            Start the timer.
            """

            self.start_time = datetime.now(UTC)
            self._start_perf_counter = perf_counter()

        def get_time(self) -> float:
            """
            Get the time taken by a process without stopping the timer.
            :return: The time taken by a process.
            """

            return self.start_time + timedelta(seconds=perf_counter() - self._start_perf_counter)

        def elapsed_time(self) -> float:
            """
            Get the elapsed time.
            :return: The elapsed time.
            """

            return (self.end_time - self.start_time).total_seconds()

        def stop(self) -> None:
            """
            Stop the timer.
            """

            self._stop_perf_counter = perf_counter()
            self.end_time = self.start_time + timedelta(seconds=self._stop_perf_counter - self._start_perf_counter)


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

        return str(request.url)
