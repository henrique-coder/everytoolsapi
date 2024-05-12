import flask
from typing import *

from static.dependencies.version import APIVersion
from static.dependencies.functions import APITools

from static.endpoints.randomizer.v2.services import Randomizer


app = flask.current_app
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
            def int_number(min_value: Any, max_value: Any) -> dict:
                timer = APITools.Timer()
                response = Randomizer.int_number(min_value, max_value)
                return APITools.gen_api_output_dict(timer.stop_timer(), response)

            @staticmethod
            def float_number(min_value: Any, max_value: Any) -> dict:
                timer = APITools.Timer()
                response = Randomizer.float_number(min_value, max_value)
                return APITools.gen_api_output_dict(timer.stop_timer(), response)
