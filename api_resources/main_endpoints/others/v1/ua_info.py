from time import perf_counter
from typing import Union
from user_agents import parse as UserAgentParser
from werkzeug.user_agent import UserAgent


def main(request_user_agent: UserAgent = None, custom_ua: Union[str, None] = None) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = {'data': dict()}

    if not custom_ua or not str(custom_ua).strip():
        ua_string = str(request_user_agent).strip()

        if not ua_string:
            return None
    else:
        ua_string = str(custom_ua).strip()

    user_agent = UserAgentParser(ua_string)

    generated_data['data']['ua_string'] = user_agent.ua_string
    generated_data['data']['os'] = {'family': user_agent.os.family, 'version': user_agent.os.version, 'version_string': user_agent.os.version_string}
    generated_data['data']['browser'] = {'family': user_agent.browser.family, 'version': user_agent.browser.version, 'version_string': user_agent.browser.version_string}
    generated_data['data']['device'] = {'family': user_agent.device.family, 'brand': user_agent.device.brand, 'model': user_agent.device.model}

    for key, value in generated_data['data'].items():
        if isinstance(value, str) and not value.strip():
            generated_data['data'][key] = None

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
