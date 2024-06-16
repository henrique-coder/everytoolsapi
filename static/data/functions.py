from flask import request, Request
from psycopg2 import Error as psycopg2Error, connect as psycopg2_connect
from time import perf_counter
from datetime import timedelta, datetime, UTC
from typing import *

from static.data.version import APIVersion


# Get the latest API version
latest_api_version = APIVersion().latest_version


class DBTools:
    """
    A class for database tools.
    """

    @staticmethod
    def initialize_db_connection(db_name: str, db_user: str, db_password: str, db_host: str, db_port: str, ssl_mode: str) -> psycopg2_connect:
        """
        Connect to a PostgreSQL database and return the connection object.
        :param db_name: The name of the database to connect to.
        :param db_user: The username to use for authentication.
        :param db_password: The password to use for authentication.
        :param db_host: The hostname of the database server.
        :param db_port: The port number to connect to.
        :param ssl_mode: The SSL mode to use for the connection.
        :return: A connection object to the database.
        """

        try:
            return psycopg2_connect(dbname=db_name, user=db_user, password=db_password, host=db_host, port=db_port, sslmode=ssl_mode)
        except psycopg2Error as e:
            raise Exception(f'Error while connecting to the database: {e}')

    class APIRequestLogs:
        """
        A class for API request logs.
        """

        @staticmethod
        def create_required_tables(conn_object: psycopg2_connect) -> None:
            """
            Create the required tables in the database.
            :param conn_object: The connection object to the database.
            :return: True if the tables were created successfully, False otherwise.
            """

            try:
                cursor = conn_object.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS api_request_logs (
                        id SERIAL PRIMARY KEY,
                        status VARCHAR(16) NOT NULL,
                        route VARCHAR(255) NOT NULL,
                        origin_ip_address INET NOT NULL,
                        created_at TIMESTAMP NOT NULL
                    );
                ''')
                conn_object.commit()
                cursor.close()
            except psycopg2Error as e:
                raise Exception(f'Error while creating tables: {e}')

        @staticmethod
        def start_request_log(conn: psycopg2_connect, route: str, origin_ip_address: str, created_at: datetime) -> None:
            """
            Log the start of a request.
            :param conn: The connection object to the database.
            :param route: The route of the current request.
            :param origin_ip_address: The origin IP address of the current request.
            :param created_at: The timestamp of the current request.
            """

            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO api_request_logs (status, route, origin_ip_address, created_at)
                    VALUES (%s, %s);
                ''', ('started', route, origin_ip_address, created_at))
                conn.commit()
                cursor.close()
            except psycopg2Error as e:
                raise Exception(f'Error while logging request start: {e}')


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
            Get the time taken by a process.
            :return: The time taken by a process.
            """

            return (datetime.now(UTC) - self.start_time).total_seconds()

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
