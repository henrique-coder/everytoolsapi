from user_agents import parse as UserAgentParser
from urllib.parse import urlparse, parse_qs
from re import compile as re_compile, findall
from collections import Counter
from langdetect import detect as detect_lang, DetectorFactory, LangDetectException
from langcodes import Language
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
                This class is a placeholder for the "/parser/user-agent" API endpoint.
                """

                endpoint_url = '/parser/user-agent/'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_day=1000)
                timeout = 1

                @staticmethod
                def run(request_data: Dict[str, Dict[Any, Any]]) -> dict:
                    """
                    This method runs the "/parser/user-agent" API endpoint.
                    :param request_data: The request data.
                    """

                    start_time = OtherTools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    # Request data validation
                    if request_data['args'].get('query'): ua_string = request_data['args']['query']
                    elif request_data['headers'].get('User-Agent'): ua_string = request_data['headers']['User-Agent']
                    else:
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

                    output_data['response'] = parsed_ua_data
                    output_data['api']['status'] = True
                    output_data['api']['elapsedTime'] = start_time.stop_timer()

                    return output_data

            class url:
                """
                This class is a placeholder for the "/parser/url" API endpoint.
                """

                endpoint_url = '/parser/url/'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_day=1000)
                timeout = 1

                @staticmethod
                def run(request_data: Dict[str, Dict[Any, Any]]) -> dict:
                    """
                    This method runs the "/parser/url" API endpoint.
                    :param request_data: The request data.
                    """

                    start_time = OtherTools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    # Request data validation
                    if request_data['args'].get('query'): url = request_data['args']['query']
                    else:
                        output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                        return output_data

                    # Main process
                    parsed_url = urlparse(url)
                    params = {key: value[0] if len(value) == 1 else value for key, value in parse_qs(parsed_url.query).items()}
                    parsed_url_data = {
                        'protocol': parsed_url.scheme,
                        'hostname': parsed_url.hostname,
                        'path': parsed_url.path,
                        'params': params,
                        'fragment': parsed_url.fragment
                    }

                    output_data['response'] = parsed_url_data
                    output_data['api']['status'] = True
                    output_data['api']['elapsedTime'] = start_time.stop_timer()

                    return output_data

            class sec_to_hms:
                """
                This class is a placeholder for the "/parser/sec-to-hms" API endpoint.
                """

                endpoint_url = '/parser/sec-to-hms/'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_day=1000)
                timeout = 1

                @staticmethod
                def run(request_data: Dict[str, Dict[Any, Any]]) -> dict:
                    """
                    This method runs the "/parser/sec-to-hms" API endpoint.
                    :param request_data: The request data.
                    """

                    start_time = OtherTools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    # Request data validation
                    if request_data['args'].get('query'):
                        try:
                            seconds = int(request_data['args']['query'])
                            if seconds < 0:
                                output_data['api']['errorMessage'] = 'The "query" parameter cannot be negative.'
                                return output_data
                        except ValueError:
                            output_data['api']['errorMessage'] = 'The "query" parameter must be an integer.'
                            return output_data
                    else:
                        output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                        return output_data

                    # Main process
                    hours, seconds = divmod(seconds, 3600)
                    minutes, seconds = divmod(seconds, 60)
                    hms_string = f'{hours:02}:{minutes:02}:{seconds:02}'

                    output_data['response'] = {'hmsString': hms_string}
                    output_data['api']['status'] = True
                    output_data['api']['elapsedTime'] = start_time.stop_timer()

                    return output_data

            class email:
                """
                This class is a placeholder for the "/parser/email" API endpoint.
                """

                endpoint_url = '/parser/email/'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_day=1000)
                timeout = 1

                @staticmethod
                def run(request_data: Dict[str, Dict[Any, Any]]) -> dict:
                    """
                    This method runs the "/parser/email" API endpoint.
                    :param request_data: The request data.
                    """

                    start_time = OtherTools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    # Request data validation
                    if request_data['args'].get('query'): email = request_data['args']['query']
                    else:
                        output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                        return output_data

                    # Main process
                    email_regex = re_compile(r'^(?P<user>[a-zA-Z0-9._%+-]+)@(?P<domain>[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$')
                    match = email_regex.match(email)

                    if not match:
                        output_data['api']['errorMessage'] = 'The e-mail address format is invalid.'
                        return output_data

                    parsed_email_data = match.groupdict()

                    output_data['response'] = parsed_email_data
                    output_data['api']['status'] = True
                    output_data['api']['elapsedTime'] = start_time.stop_timer()

                    return output_data

            class text_counter:
                """
                This class is a placeholder for the "/parser/text-counter" API endpoint.
                """

                endpoint_url = '/parser/text-counter/'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_day=1000)
                timeout = 1

                @staticmethod
                def run(request_data: Dict[str, Dict[Any, Any]]) -> dict:
                    """
                    This method runs the "/parser/text-counter" API endpoint.
                    :param request_data: The request data.
                    """

                    start_time = OtherTools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    # Request data validation
                    if request_data['args'].get('query'): text = request_data['args']['query']
                    else:
                        output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                        return output_data

                    # Main process
                    lowercase_counts = dict(Counter(char for char in text if char.islower()))
                    uppercase_counts = dict(Counter(char for char in text if char.isupper()))
                    digit_counts = dict(Counter(char for char in text if char.isdigit()))
                    letter_counts = dict(Counter(char for char in text if char.isalpha()))
                    other_symbol_counts = dict(Counter(char for char in text if not char.isalnum() and not char.isspace()))
                    word_counts = dict(Counter(findall(r'\b[a-zA-Z]+(?:\'[a-zA-Z]+)*\b', text.lower())))
                    space_count = int(text.count(' '))

                    output_data['response'] = {
                        'counts': {
                            'lowercase': {
                                'total': len(lowercase_counts),
                                'characters': lowercase_counts,
                            },
                            'uppercase': {
                                'total': len(uppercase_counts),
                                'characters': uppercase_counts,
                            },
                            'numbers': {
                                'total': len(digit_counts),
                                'characters': digit_counts,
                            },
                            'letters': {
                                'total': len(letter_counts),
                                'characters': letter_counts,
                            },
                            'otherSymbols': {
                                'total': len(other_symbol_counts),
                                'characters': other_symbol_counts,
                            },
                            'words': {
                                'total': len(word_counts),
                                'characters': word_counts,
                            },
                            'spaces': space_count,
                        },
                    }
                    output_data['api']['status'] = True
                    output_data['api']['elapsedTime'] = start_time.stop_timer()

                    return output_data

            class text_lang_detector:
                """
                This class is a placeholder for the "/parser/text-lang-detector" API endpoint.
                """

                endpoint_url = '/parser/text-lang-detector/'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=4, per_day=800)
                timeout = 1

                @staticmethod
                def run(request_data: Dict[str, Dict[Any, Any]]) -> dict:
                    """
                    This method runs the "/parser/text-lang-detector" API endpoint.
                    :param request_data: The request data.
                    """

                    start_time = OtherTools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    # Request data validation
                    if request_data['args'].get('query'): text = request_data['args']['query']
                    else:
                        output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                        return output_data

                    # Main process
                    DetectorFactory.seed = 0

                    try: detected_lang = detect_lang(text)
                    except LangDetectException:
                        output_data['api']['errorMessage'] = "There aren't enough resources in the text to detect your language."
                        return output_data

                    output_data['response'] = {'detectedLangCode': detected_lang, 'detectedLangName': Language.get(detected_lang).display_name('en')}
                    output_data['api']['status'] = True
                    output_data['api']['elapsedTime'] = start_time.stop_timer()

                    return output_data
