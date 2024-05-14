from typing import *

from static.dependencies.version import APIVersion
from static.dependencies.functions import APITools

from static.endpoints.randomizer.v2 import Randomizer
from static.endpoints.parser.v2 import Parser
from static.endpoints.requester.v2 import Requester
from static.endpoints.scraper.v2 import Scraper


latest_api_version = APIVersion.Latest().version


class Endpoints:
    @staticmethod
    def api_version(version: str) -> Any:
        if version == 'v1': return Endpoints.V1
        elif version == 'v2': return Endpoints.V2
        else: return Endpoints.UnknownAPIVersion

    class Info:
        pass

    class UnknownAPIVersion:
        @staticmethod
        def get_status(version: str) -> Dict[str, Union[bool, str]]:
            return APITools.gen_api_status_response_dict(False, version, latest_api_version)

    class V1:
        @staticmethod
        def get_status(version: str) -> Dict[str, Union[bool, str]]:
            return APITools.gen_api_status_response_dict(True, version, latest_api_version)

    class V2:
        @staticmethod
        def get_status(version: str) -> Dict[str, Union[bool, str]]:
            return APITools.gen_api_status_response_dict(True, version, latest_api_version)

        class Randomizer:
            class int_number:
                info = {'methods': ['GET'], 'ratelimit': (0, 120, 6000, 16000), 'cache': 1}

                @staticmethod
                def run(input_values: Dict[str, Optional[Any]]) -> dict:
                    timer = APITools.Timer()
                    response = Randomizer.int_number(APITools.clean_values_from_dict(input_values))
                    return APITools.gen_api_output_dict(timer.stop_timer(), response)

            class float_number:
                info = {'methods': ['GET'], 'ratelimit': (0, 120, 6000, 16000), 'cache': 1}

                @staticmethod
                def run(input_values: Dict[str, Optional[Any]]) -> dict:
                    timer = APITools.Timer()
                    response = Randomizer.float_number(APITools.clean_values_from_dict(input_values))
                    return APITools.gen_api_output_dict(timer.stop_timer(), response)

        class Parser:
            class user_agent:
                info = {'methods': ['GET'], 'ratelimit': (1, 60, 4000, 12000), 'cache': 3600}

                @staticmethod
                def run(input_values: Dict[str, Optional[Any]]) -> dict:
                    timer = APITools.Timer()
                    response = Parser.user_agent(APITools.clean_values_from_dict(input_values))
                    return APITools.gen_api_output_dict(timer.stop_timer(), response)

        class Requester:
            class ip_address:
                info = {'methods': ['GET'], 'ratelimit': (1, 60, 4000, 8000), 'cache': 43200}

                @staticmethod
                def run(input_values: Dict[str, Optional[Any]]) -> dict:
                    timer = APITools.Timer()
                    response = Requester.ip_address(APITools.clean_values_from_dict(input_values))
                    return APITools.gen_api_output_dict(timer.stop_timer(), response)

        class Scraper:
            class media_youtube_com:
                info = {'methods': ['GET'], 'ratelimit': (1, 30, 400, 1000), 'cache': 14400}

                @staticmethod
                def run(input_values: Dict[str, Optional[Any]]) -> dict:
                    timer = APITools.Timer()
                    response = Scraper.media_youtube_com(APITools.clean_values_from_dict(input_values))
                    return APITools.gen_api_output_dict(timer.stop_timer(), response)
