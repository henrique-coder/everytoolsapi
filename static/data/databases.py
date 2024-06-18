from psycopg2 import connect as psycopg2_connect, Error as psycopg2Error, extensions as psycopg2_extensions
from datetime import datetime
from typing import Any, Dict


class APIRequestLogs:
    """
    A class for API request logs.
    """

    def __init__(self) -> None:
        """
        Initialize the APIRequestLogs class.
        """

        self.client = None

    def connect(self, db_name: str, db_user: str, db_password: str, db_host: str, db_port: str, ssl_mode: str) -> None:
        """
        Connect to a PostgreSQL database and return the connection object.
        :param db_name: The name of the database to connect to.
        :param db_user: The username to use for authentication.
        :param db_password: The password to use for authentication.
        :param db_host: The hostname of the database server.
        :param db_port: The port number to connect to.
        :param ssl_mode: The SSL mode to use for the connection.
        """

        try:
            self.client = psycopg2_connect(dbname=db_name, user=db_user, password=db_password, host=db_host, port=db_port, sslmode=ssl_mode)
        except psycopg2Error as e:
            raise Exception(f'Error while connecting to the database: {e}')

    @staticmethod
    def _insert_into(cursor: psycopg2_extensions.cursor, table_name: str, data: Dict[str, str], return_column: str = None) -> Any:
        """
        Get the insert query for the given table and data.
        :param cursor: The cursor object to use for the query.
        :param table_name: The name of the table to insert data into.
        :param data: The data to insert into the table.
        :param return_column: The column to return after inserting the data.
        :return: The insert query for the given table and data.
        """

        query = f'''
            INSERT INTO {table_name} ({', '.join(data.keys())})
            VALUES ('{'\', \''.join(str(v) for v in data.values())}')
        '''

        if return_column:
            query += f' RETURNING {return_column}'
            cursor.execute(query)
            return cursor.fetchone()[0]

        cursor.execute(query)

    def create_required_tables(self) -> None:
        """
        Create the required tables in the database.
        """

        try:
            cursor = self.client.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_requests (
                    id SERIAL PRIMARY KEY,
                    route VARCHAR(255) NOT NULL,
                    params VARCHAR(255) NOT NULL,
                    origin_ip_address INET NOT NULL,
                    created_at TIMESTAMP NOT NULL
                );
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_request_logs (
                    id SERIAL PRIMARY KEY,
                    api_request_id INT REFERENCES api_requests(id),
                    status VARCHAR(16) NOT NULL,
                    created_at TIMESTAMP NOT NULL
                );
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_request_exceptions (
                    id SERIAL PRIMARY KEY,
                    api_request_id INT REFERENCES api_requests(id),
                    message VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP NOT NULL
                );
            ''')
            self.client.commit()
            cursor.close()
        except psycopg2Error as e:
            raise Exception(f'Error while creating tables: {e}')

    def start_request(self, request_data: Dict[str, Dict[Any, Any]], created_at: datetime) -> None:
        """
        Log the start of a request.
        :param request_data: The data of the request.
        :param created_at: The timestamp of the current request.
        """

        try:
            cursor = self.client.cursor()

            # Create request in PostgreSQL and get the generated ID
            print(f'[debug] request_data: {request_data}')
            data = {
                'route': request_data['pathRoute'],
                'params': '?' + '&'.join(f'{k}={v}' for k, v in request_data['args'].items()),
                'origin_ip_address': request_data['ipAddress'],
                'created_at': created_at
            }
            request_id = self._insert_into(cursor, 'api_requests', data, return_column='id')

            # Log "started" status
            self.update_request_status('started', request_id, created_at)

            self.client.commit()
            cursor.close()
            return request_id
        except psycopg2Error as e:
            raise Exception(f'Error while logging request start: {e}')

    def update_request_status(self, status: str, request_id: int, created_at: datetime) -> None:
        """
        Log the end of a request.
        :param status: The status of the request.
        :param request_id: The ID of the request to update.
        :param created_at: The timestamp of the current request.
        """

        try:
            cursor = self.client.cursor()

            # Log new status
            data = {
                'api_request_id': request_id,
                'status': status,
                'created_at': created_at,
            }
            self._insert_into(cursor, 'api_request_logs', data)

            self.client.commit()
            cursor.close()
        except psycopg2Error as e:
            raise Exception(f'Error while logging request start: {e}')

    def log_exception(self, request_id: int, message: str, created_at: datetime) -> None:
        """
        Log an exception that occurred during the request.
        :param request_id: The ID of the request that caused the exception.
        :param message: The exception message.
        :param created_at: The timestamp of the current request.
        """

        try:
            cursor = self.client.cursor()

            # Log exception
            data = {
                'api_request_id': request_id,
                'message': message,
                'created_at': created_at,
            }
            self._insert_into(cursor, 'api_request_exceptions', data)

            # Log "exception" status
            self.update_request_status('exception', request_id, created_at)

            self.client.commit()
            cursor.close()
        except psycopg2Error as e:
            raise Exception(f'Error while logging exception: {e}')
