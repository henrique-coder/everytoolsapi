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
            @staticmethod
            def int_number(_min: AnyStr, _max: AnyStr) -> dict:
                timer = APITools.Timer()
                response = Randomizer.int_number(APITools.remove_empty_values_from_dict({'min': _min, 'max': _max}))
                return APITools.gen_api_output_dict(timer.stop_timer(), response)

            @staticmethod
            def float_number(_min: AnyStr, _max: AnyStr) -> dict:
                timer = APITools.Timer()
                response = Randomizer.float_number(APITools.remove_empty_values_from_dict({'min': _min, 'max': _max}))
                return APITools.gen_api_output_dict(timer.stop_timer(), response)

        class Parser:
            @staticmethod
            def user_agent(remote_user_agent_header: AnyStr, query: AnyStr) -> dict:
                timer = APITools.Timer()
                response = Parser.user_agent(APITools.remove_empty_values_from_dict({'remoteUserAgentHeader': remote_user_agent_header, 'query': query}))
                return APITools.gen_api_output_dict(timer.stop_timer(), response)

        class Requester:
            @staticmethod
            def ip_address(remote_ip_address_header: AnyStr, query: AnyStr) -> dict:
                timer = APITools.Timer()
                response = Requester.ip_address(APITools.remove_empty_values_from_dict({'remoteIpAddressHeader': remote_ip_address_header, 'query': query}))
                return APITools.gen_api_output_dict(timer.stop_timer(), response)

        class Scraper:
            @staticmethod
            def youtube_com(query: AnyStr) -> dict:
                timer = APITools.Timer()
                response = Scraper.youtube_com(APITools.remove_empty_values_from_dict({'query': query}))
                return APITools.gen_api_output_dict(timer.stop_timer(), response)
