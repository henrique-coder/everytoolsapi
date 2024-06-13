import flask
from collections import defaultdict
from time import time, perf_counter
from typing import *

from static.data.version import APIVersion


# Get the latest API version
latest_api_version = APIVersion().get_latest_version()


class OtherTools:
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
            """

            return float(round(data, 3))

        def get_time(self) -> float:
            """
            Get the time taken by a process.
            """

            return OtherTools.Timer._format_time(perf_counter() - self._start_time)

        def stop_timer(self, return_time: bool = True) -> Optional[float]:
            """
            Stop the timer and get the time taken by a process.
            :param return_time: A boolean to determine if the time taken by a process should be returned.
            """

            if return_time: return OtherTools.Timer._format_time(perf_counter() - self._start_time)
            else: return None

class APITools:
    pass


class CacheTools:
    @staticmethod
    def get_cache_key(*args, **kwargs) -> str:
        """
        Generate a cache key for the current request.
        """

        return str(flask.request.url)
