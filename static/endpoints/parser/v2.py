from user_agents import parse as UserAgentParser
from typing import *

from static.dependencies.functions import APITools
from static.dependencies.exceptions import Exceptions


class Parser:
    @staticmethod
    def user_agent(input_values: Dict[str, Optional[Any]]) -> dict:
        output_dict = APITools.get_default_output_dict()

        # Input parameter validation
        if not input_values['remoteUserAgentHeader'] and not input_values['query']:
            output_dict['errorMessage'] = Exceptions.EMPTY_PARAMETERS_VALUE.message.format('query')
            return output_dict

        if input_values['query']: ua_string = input_values['query']
        else: ua_string = input_values['remoteUserAgentHeader']

        # Main process
        user_agent = UserAgentParser(ua_string)
        output_data = {
            'ua_string': user_agent.ua_string,
            'os': {
                'family': user_agent.os.family,
                'version': user_agent.os.version,
                'version_string': user_agent.os.version_string
            },
            'browser': {
                'family': user_agent.browser.family,
                'version': user_agent.browser.version,
                'version_string': user_agent.browser.version_string
            },
            'device': {
                'family': user_agent.device.family,
                'brand': user_agent.device.brand,
                'model': user_agent.device.model
            }
        }

        for key, value in output_data.items():
            if isinstance(value, str) and not value.strip(): output_data[key] = None

        output_dict['success'], output_dict['response'] = True, output_data
        return output_dict
