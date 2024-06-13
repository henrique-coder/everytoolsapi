from user_agents import parse as UserAgentParser
from typing import *

from static.data.functions import OtherTools, APITools, LimiterTools


class APIEndpoints:
    """
    This class is a placeholder for the API endpoints.
    """

    class v2:
        """
        This class is a placeholder for the v2 API endpoints.
        """

        class parser:
            """
            This class is a placeholder for the "parser" API endpoints.
            """

            class user_agent:
                """
                This class is a placeholder for the "user_agent" API endpoint.
                """

                endpoint_url = '/parser/user-agent/'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_day=1000)
                timeout = 1

                @staticmethod
                def run(request_data: Dict[str, Dict[Any, Any]]) -> Any:
                    start_time = OtherTools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    # Request data validation
                    if request_data['args'].get('query'): ua_string = request_data['args']['query']
                    elif request_data['headers'].get('User-Agent'): ua_string = request_data['headers']['User-Agent']
                    else:
                        output_data['api']['status'] = False
                        output_data['api']['errorMessage'] = 'No "query" parameter or "User-Agent" header found in the request.'
                        return output_data

                    # Main process
                    user_agent = UserAgentParser(ua_string)
                    parsed_ua_data = {
                        'uaString': user_agent.ua_string,
                        'os': {
                            'family': user_agent.os.family,
                            'version': user_agent.os.version,
                            'versionString': user_agent.os.version_string
                        },
                        'browser': {
                            'family': user_agent.browser.family,
                            'version': user_agent.browser.version,
                            'versionString': user_agent.browser.version_string
                        },
                        'device': {
                            'family': user_agent.device.family,
                            'brand': user_agent.device.brand,
                            'model': user_agent.device.model
                        }
                    }

                    output_data['api']['status'] = True
                    output_data['response'] = parsed_ua_data
                    output_data['api']['elapsedTime'] = start_time.stop_timer()

                    return output_data
