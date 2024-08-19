# Built-in modules
from collections import Counter
from re import compile as re_compile, sub as re_sub, findall as re_findall, search as re_search
from subprocess import run as run_subprocess, CalledProcessError as SubprocessCalledProcessError
from typing import Any, AnyStr, Optional, Union, List, Dict, Tuple, Type
from urllib.parse import urlparse, parse_qs, unquote, urlencode, unquote_plus

# Third-party modules
from bs4 import BeautifulSoup
from faker import Faker
from googletrans import Translator
from httpx import get, post, HTTPError
from instaloader import Instaloader, Post as instagram_post
from langdetect import detect as lang_detect, DetectorFactory, LangDetectException
from lxml import html
from orjson import loads as orjson_loads, JSONDecodeError
from psycopg2 import connect as psycopg2_connect
from sclib import SoundcloudAPI, Track as SoundcloudTrack
from selectolax.parser import HTMLParser
from unicodedata import normalize
from user_agents import parse as UserAgentParser
from validators import url as is_valid_url
from yt_dlp import YoutubeDL, DownloadError as YTDLPDownloadError

# Local modules
from static.data.functions import APITools, LimiterTools


# Constants
fake = Faker()
DetectorFactory.seed = 0

# Helper functions
def get_value(data: Dict[Any, Any], key: Any, fallback_key: Any = None, convert_to: Type = None, default_to: Any = None) -> Any:
    """
    Get a value from a dictionary, with optional fallback key, conversion and default value.
    :param data: The dictionary to search for the key.
    :param key: The key to search for in the dictionary.
    :param fallback_key: The fallback key to search for in the dictionary if the main key is not found.
    :param convert_to: The type to convert the value to. If the conversion fails, return the default value. If None, return the value as is.
    :param default_to: The default value to return if the key is not found.
    :return: The value from the dictionary, or the default value if the key is not found.
    """

    try:
        value = data[key]
    except KeyError:
        if fallback_key is not None:
            try:
                value = data[fallback_key]
            except KeyError:
                return default_to
        else:
            return default_to

    if convert_to is not None:
        try:
            value = convert_to(value)
        except (ValueError, TypeError):
            return default_to

    return value

def format_string(query: AnyStr, max_length: int = 128) -> Optional[str]:
    """
    Format a string to be used as a filename or directory name. Remove special characters, limit length etc.
    :param query: The string to be formatted.
    :param max_length: The maximum length of the formatted string. If the string is longer, it will be truncated.
    :return: The formatted string. If the input string is empty or None, return None.
    """

    if not query or not query.strip():
        return None

    normalized_string = normalize('NFKD', str(query)).encode('ASCII', 'ignore').decode('utf-8')
    sanitized_string = re_sub(r'\s+', ' ', re_sub(r'[^a-zA-Z0-9\-_()[\]{}!$#+;,. ]', '', normalized_string)).strip()

    if len(sanitized_string) > max_length:
        cutoff = sanitized_string[:max_length].rfind(' ')
        sanitized_string = sanitized_string[:cutoff] if cutoff != -1 else sanitized_string[:max_length]

    return sanitized_string


# Main endpoints classes
class APIEndpoints:
    class v2:
        @staticmethod
        def status(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
            timer = APITools.Timer()
            output_data = APITools.get_default_api_output_dict()

            api_request_id = db_client.start_request(request_data, timer.start_time)

            timer.stop()

            output_data['response'] = {'status': 'ok', 'message': 'API server is successfully running.'}
            output_data['api']['status'] = True
            output_data['api']['elapsedTime'] = timer.elapsed_time()

            db_client.update_request_status('success', api_request_id, timer.end_time)

            return output_data, 200

        class useragent:
            ready_to_production = True

            endpoint_url = 'useragent'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_min=300, per_day=1000000)
            cache_timeout = 1

            title = 'User-Agent Parser'
            description = 'Parse User-Agent string to get OS, browser, and device information. If no "query" parameter is provided, the User-Agent header will be used.'
            parameters = {
                'query': {'description': 'User-Agent string to be parsed.', 'required': False, 'type': 'string'}
            }
            expected_output = {
                'browser': {
                    'family': 'string',
                    'version': 'string',
                    'versionString': 'string'
                },
                'device': {
                    'brand': 'string',
                    'family': 'string',
                    'model': 'string'
                },
                'isBot': 'boolean',
                'isComputer': 'boolean',
                'isEmailClient': 'boolean',
                'isMobile': 'boolean',
                'isTablet': 'boolean',
                'isTouchCapable': 'boolean',
                'os': {
                    'family': 'string',
                    'version': 'string',
                    'versionString': 'string'
                },
                'uaString': 'string'
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    ua_string = request_data['args']['query']
                elif request_data['headers'].get('User-Agent'):
                    ua_string = request_data['headers']['User-Agent']
                else:
                    output_data['api'][
                        'errorMessage'] = 'No "query" parameter or "User-Agent" header found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                # Main process
                user_agent = UserAgentParser(ua_string)
                parsed_ua_data = {
                    'browser': {
                        'family': user_agent.browser.family,
                        'version': user_agent.browser.version,
                        'versionString': user_agent.browser.version_string
                    },
                    'device': {
                        'brand': user_agent.device.brand,
                        'family': user_agent.device.family,
                        'model': user_agent.device.model
                    },
                    'isBot': user_agent.is_bot,
                    'isComputer': user_agent.is_pc,
                    'isEmailClient': user_agent.is_email_client,
                    'isMobile': user_agent.is_mobile,
                    'isTablet': user_agent.is_tablet,
                    'isTouchCapable': user_agent.is_touch_capable,
                    'os': {
                        'family': user_agent.os.family,
                        'version': user_agent.os.version,
                        'versionString': user_agent.os.version_string
                    },
                    'uaString': user_agent.ua_string,

                }

                timer.stop()

                output_data['response'] = parsed_ua_data
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class url:
            ready_to_production = True

            endpoint_url = 'url'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_min=300, per_day=1000000)
            cache_timeout = 1

            title = 'URL Parser'
            description = 'Parse URL to get protocol, hostname, path, parameters, and fragment information.'
            parameters = {
                'query': {'description': 'URL to be parsed.', 'required': True, 'type': 'string'}
            }
            expected_output = {
                'fragment': 'string',
                'hostname': 'string',
                'params': 'dict',
                'path': 'string',
                'protocol': 'string'
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    url = request_data['args']['query']
                else:
                    output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

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

                timer.stop()

                output_data['response'] = parsed_url_data
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class seconds_to_hhmmss_format_converter:
            ready_to_production = True

            endpoint_url = 'seconds-to-hh:mm:ss-format-converter'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_min=300, per_day=1000000)
            cache_timeout = 1

            title = 'Seconds to HH:MM:SS format Converter'
            description = 'Convert seconds to HH:MM:SS format.'
            parameters = {
                'query': {'description': 'Seconds to be converted.', 'required': True, 'type': 'integer'}
            }
            expected_output = {
                'hmsString': 'string'
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    try:
                        seconds = int(request_data['args']['query'])

                        if seconds < 0:
                            output_data['api']['errorMessage'] = 'The "query" parameter cannot be negative.'
                            return output_data, 400
                    except ValueError:
                        output_data['api']['errorMessage'] = 'The "query" parameter must be an integer.'
                        return output_data, 400
                else:
                    output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                # Main process
                hours, seconds = divmod(seconds, 3600)
                minutes, seconds = divmod(seconds, 60)
                hms_string = f'{hours:02}:{minutes:02}:{seconds:02}'

                timer.stop()

                output_data['response'] = {'hmsString': hms_string}
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class email:
            ready_to_production = True

            endpoint_url = 'email'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_min=300, per_day=1000000)
            cache_timeout = 1

            title = 'E-Mail Address Parser'
            description = 'Parse e-mail address to get user and domain information.'
            parameters = {
                'query': {'description': 'E-mail address to be parsed.', 'required': True, 'type': 'string'}
            }
            expected_output = {
                'domain': 'string',
                'separator': 'string',
                'user': 'string'
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    email = request_data['args']['query']
                else:
                    output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                email_regex = re_compile(r'^(?P<user>[a-zA-Z0-9._%+-]+)@(?P<domain>[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$')
                match = email_regex.match(email)

                if not match:
                    output_data['api']['errorMessage'] = 'The e-mail address format is invalid.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                # Main process
                parsed_email_data = match.groupdict()
                parsed_email_data.update({'separator': '@'})

                timer.stop()

                output_data['response'] = parsed_email_data
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class string_counter:
            ready_to_production = True

            endpoint_url = 'string-counter'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=5, per_min=300, per_day=1000000)
            cache_timeout = 1

            title = 'String Counter'
            description = 'Count the number of characters, words, and many other elements in a text.'
            parameters = {
                'query': {'description': 'Text to be analyzed.', 'required': True, 'type': 'string'}
            }
            expected_output = {
                'letters': {
                    'characters': 'dict',
                    'total': 'integer'
                },
                'lowercase': {
                    'characters': 'dict',
                    'total': 'integer'
                },
                'numbers': {
                    'characters': 'dict',
                    'total': 'integer'
                },
                'otherSymbols': {
                    'characters': 'dict',
                    'total': 'integer'
                },
                'spaces': 'integer',
                'uppercase': {
                    'characters': 'dict',
                    'total': 'integer'
                },
                'words': {
                    'characters': 'dict',
                    'total': 'integer'
                }
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    text = request_data['args']['query']
                else:
                    output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                # Main process
                lowercase_counts = dict(Counter(char for char in text if char.islower()))
                uppercase_counts = dict(Counter(char for char in text if char.isupper()))
                digit_counts = dict(Counter(char for char in text if char.isdigit()))
                letter_counts = dict(Counter(char for char in text if char.isalpha()))
                other_symbol_counts = dict(Counter(char for char in text if not char.isalnum() and not char.isspace()))
                word_counts = dict(Counter(re_findall(r'\b[a-zA-Z]+(?:\'[a-zA-Z]+)*\b', text.lower())))
                space_count = int(text.count(' '))

                timer.stop()

                output_data['response'] = {
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
                }
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class language_detector:
            ready_to_production = True

            endpoint_url = 'language-detector'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=4, per_min=120, per_day=500000)
            cache_timeout = 600

            title = 'Language Detector'
            description = 'Detects the predominant language in a text.'
            parameters = {
                'query': {'description': 'Text to be analyzed.', 'required': True, 'type': 'string'}
            }
            expected_output = {
                'detectedLanguageCode': 'string'
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    text = request_data['args']['query']
                else:
                    output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                # Main process
                try:
                    detected_lang = lang_detect(text)
                except LangDetectException:
                    output_data['api']['errorMessage'] = "There aren't enough resources in the text to detect your language."
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                timer.stop()

                output_data['response'] = {'detectedLanguageCode': detected_lang}
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class translator:
            ready_to_production = True

            endpoint_url = 'translator'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=120, per_day=500000)
            cache_timeout = 1  # 600

            title = 'Translator'
            description = 'Translate any text from one language to another.'
            parameters = {
                'query': {'description': 'Text to be translated.', 'required': True, 'type': 'string'},
                'source': {'description': 'Source language code (e.g., "pt" for Portuguese). If not provided, the language will be automatically detected.', 'required': False, 'type': 'string'},
                'destination': {'description': 'Destination language code (e.g., "en" for English).', 'required': True, 'type': 'string'}
            }
            expected_output = {
                'translatedText': 'string'
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    text = request_data['args']['query']
                else:
                    output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                if request_data['args'].get('destination'):
                    destination_lang = str(request_data['args']['destination']).replace('-', '_')
                else:
                    output_data['api']['errorMessage'] = 'No "destination" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                source_lang = request_data['args'].get('source', None)

                # Main process
                try:
                    translator = Translator()
                    translated_text = translator.translate(text, src='auto' if not source_lang else str(source_lang).replace('-', '_'), dest=destination_lang)
                except ValueError as e:
                    output_data['api']['errorMessage'] = str(e).capitalize()
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                timer.stop()

                output_data['response'] = {'translatedText': translated_text.text}
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class ip:
            ready_to_production = True

            endpoint_url = 'ip'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=4, per_min=120, per_day=500000)
            cache_timeout = 1

            title = 'My IP Address'
            description = 'Get the IP address of the client making the request.'
            parameters = {}
            expected_output = {
                'originIpAddress': 'string'
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data.get('ipAddress'):
                    ip = request_data['ipAddress']
                else:
                    output_data['api']['errorMessage'] = 'Your IP address was not found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                # Main process
                timer.stop()

                output_data['response'] = {'originIpAddress': ip}
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class latest_ffmpeg_build:
            ready_to_production = True

            endpoint_url = 'latest-ffmpeg-build'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=60, per_day=500000)
            cache_timeout = 43200

            title = 'Retrieve Latest FFmpeg Build URL'
            description = 'Retrieve the latest FFmpeg build URL from the official repository based on the specified parameters.'
            parameters = {
                'os': {'description': 'Operating system (options: "windows", "linux").', 'required': False, 'type': 'string'},
                'arch': {'description': 'Architecture (options: "amd32", "amd64", "arm32", "arm64").', 'required': False, 'type': 'string'},
                'license': {'description': 'License type (options: "gpl", "lgpl").', 'required': False, 'type': 'string'},
                'shared': {'description': 'Whether the FFmpeg build is shared or not (options: "true", "false").', 'required': False, 'type': 'boolean'}
            }
            expected_output = {
                'matchedBuildUrls': 'list'
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                os = request_data['args'].get('os')
                arch = request_data['args'].get('arch')
                license_name = request_data['args'].get('license')
                shared = request_data['args'].get('shared')

                # Main process
                try:
                    response = get('https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest', headers={'User-Agent': fake.user_agent(), 'X-Forwarded-For': fake.ipv4_public()}, timeout=10)
                except HTTPError:
                    output_data['api']['errorMessage'] = 'Some error occurred in our systems during the data search. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                if response.status_code != 200 or not response.json():
                    output_data['api']['errorMessage'] = 'Some external error occurred during the data search. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                response_data = dict(response.json())

                class CheckBuildVersion:
                    os = {
                        'windows': lambda build: '-win' in build,
                        'linux': lambda build: '-linux' in build,
                        None: lambda build: True,
                    }
                    arch = {
                        'amd32': lambda build: 'arm' not in build and '32-' in build,
                        'amd64': lambda build: 'arm' not in build and '64-' in build,
                        'arm32': lambda build: 'arm32' in build,
                        'arm64': lambda build: 'arm64' in build,
                        None: lambda build: True,
                    }
                    license_name = {
                        'gpl': lambda build: '-gpl' in build,
                        'lgpl': lambda build: '-lgpl' in build,
                        None: lambda build: True,
                    }
                    shared = {
                        True: lambda build: '-shared' in build,
                        False: lambda build: '-shared' not in build,
                        None: lambda build: True,
                    }

                if os and os not in CheckBuildVersion.os.keys():
                    valid_os = [key for key in CheckBuildVersion.os.keys() if key is not None]
                    output_data['api']['errorMessage'] = f'The "os" parameter must be one of the following: \"{"\", \"".join(valid_os)}\"'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400
                elif arch and arch not in CheckBuildVersion.arch.keys():
                    valid_arch = [key for key in CheckBuildVersion.arch.keys() if key is not None]
                    output_data['api']['errorMessage'] = f'The "arch" parameter must be one of the following: \"{"\", \"".join(valid_arch)}\"'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400
                elif license_name and license_name not in CheckBuildVersion.license_name.keys():
                    valid_license = [key for key in CheckBuildVersion.license_name.keys() if key is not None]
                    output_data['api']['errorMessage'] = f'The "license" parameter must be one of the following: \"{"\", \"".join(valid_license)}\"'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400
                match shared:
                    case 'true': shared = True
                    case 'false': shared = False
                    case None: shared = None
                    case _:
                        output_data['api']['errorMessage'] = 'The "shared" parameter must be a boolean: "true" or "false".'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 400

                builds = list()
                build_names = [build_data['name'] for build_data in response_data.get('assets', list())]

                for build_name in build_names:
                    if (
                            build_name.startswith('ffmpeg-master-latest-') and
                            (os is None or CheckBuildVersion.os[os](build_name)) and
                            (arch is None or CheckBuildVersion.arch[arch](build_name)) and
                            (license_name is None or CheckBuildVersion.license_name[license_name](build_name)) and
                            (shared is None or CheckBuildVersion.shared[shared](build_name))
                    ):
                        builds.append(f'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/{build_name}')

                matched_build_urls = list(set(builds))

                if not matched_build_urls:
                    output_data['api']['errorMessage'] = 'No FFmpeg build found with the specified parameters.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 404

                timer.stop()

                output_data['response'] = {'matchedBuildUrls': matched_build_urls}
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class ffprobe_a_video:
            ready_to_production = True

            endpoint_url = 'ffprobe-a-video'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=120, per_day=500000)
            cache_timeout = 3600

            title = 'FFprobe a Video URL'
            description = 'Analyze a video URL using FFprobe to get its metadata.'
            parameters = {
                'query': {'description': 'Video URL to be analyzed.', 'required': True, 'type': 'string'}
            }
            expected_output = {
                'format': 'dict',
                'streams': 'list'
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    url = request_data['args']['query']
                else:
                    output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                # Main process
                ffprobe_command = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', url]

                try:
                    process_output = run_subprocess(ffprobe_command, capture_output=True, text=True, check=True)
                    media_data = orjson_loads(process_output.stdout.encode())
                except SubprocessCalledProcessError:
                    output_data['api']['errorMessage'] = 'Invalid video URL provided. Please check the URL and try again.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400
                except (IndexError, KeyError):
                    output_data['api']['errorMessage'] = 'No video data found in the URL provided.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                timer.stop()

                output_data['response'] = media_data
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class scrap_google_search_results:
            ready_to_production = True

            endpoint_url = 'scrap-google-search-results'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=1, per_min=30, per_day=500000)
            cache_timeout = 3600

            title = 'Google Search Results Scraper'
            description = 'Scrapes Google search results for a given query.'
            parameters = {
                'query': {'description': 'Search query.', 'required': True, 'type': 'string'},
                'results': {'description': 'Number of search results to be returned (max: 50). Default: 20.', 'required': False, 'type': 'integer'},
                'language': {'description': 'Language code for the search results. Default: "en-US".', 'required': False, 'type': 'string'}
            }
            expected_output = {
                'searchResults': 'list'
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    query = request_data['args']['query']
                else:
                    output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                results = request_data['args'].get('results', 20)
                if not results: results = 20

                language = request_data['args'].get('language', 'en-US')

                try:
                    results = int(results)

                    if results < 1:
                        output_data['api']['errorMessage'] = 'The "results" parameter must be greater than 0.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 400
                    elif results > 50:
                        output_data['api']['errorMessage'] = 'The "results" parameter must be less than or equal to 50.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 400
                except ValueError:
                    output_data['api']['errorMessage'] = 'The "results" parameter must be an integer.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                # Main process
                base_url = 'https://www.google.com/search'
                params = {'q': query, 'num': results, 'hl': language, 'start': 0}
                headers = {
                    'Accept': 'text/html',
                    'User-Agent': fake.user_agent(),
                    'X-Forwarded-For': fake.ipv4_public()
                }

                raw_response = get(base_url, params=params, headers=headers, timeout=20)
                tree = HTMLParser(raw_response.content)

                extracted_results = []
                result_quantity = 0

                for node in tree.css('a[href^="/url?q="]'):
                    clean_url = unquote(urlparse(node.attributes['href']).query.split('&')[0].split('q=')[1])

                    if not is_valid_url(clean_url):
                        continue

                    extracted_results.append({'title': node.text(strip=True), 'url': clean_url})
                    result_quantity += 1

                    if result_quantity >= results:
                        break

                timer.stop()

                output_data['response'] = {'searchResults': extracted_results}
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class scrap_instagram_reels:
            ready_to_production = True

            endpoint_url = 'scrap-instagram-reels'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=60, per_day=500000)
            cache_timeout = 43200

            title = 'Instagram Reels URL Scraper'
            description = 'Scrapes Instagram Reel URL to get the media and thumbnail URLs.'
            parameters = {
                'query': {'description': 'Instagram Reels URL.', 'required': True, 'type': 'string'}
            }
            expected_output = {
                'filename': 'string',
                'mediaUrl': 'string',
                'thumbnailUrl': 'string'
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    query = request_data['args']['query']
                else:
                    output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                def is_valid_instagram_reel_url(query: str) -> bool:
                    """
                    Check if the URL is a valid Instagram Reels URL.
                    :param query: URL to be checked.
                    :return: True if the URL is a valid Instagram Reels URL, False otherwise.
                    """

                    pattern = re_compile(r'^(https?://)?(www\.)?instagram\.com(/[^/]+)?/(reels?|p)/[A-Za-z0-9_-]+/?(\?.*)?$')
                    return bool(pattern.match(query))

                def extract_instagram_reel_id(query: str) -> Optional[str]:
                    """
                    Extract the ID from a valid Instagram Reels URL.
                    :param query: URL to be checked.
                    :return: The ID of the Instagram Reel if the URL is valid, None otherwise.
                    """

                    pattern = re_compile(r'^(https?://)?(www\.)?instagram\.com(/[^/]+)?/(reels?|p)/([A-Za-z0-9_-]+)/?(\?.*)?$')
                    match = pattern.match(query)

                    if match:
                        return str(match.group(5))

                    return None

                if not is_valid_instagram_reel_url(query):
                    output_data['api']['errorMessage'] = 'The URL provided is not a valid Instagram Reels URL.'
                    return output_data, 400

                reel_id = extract_instagram_reel_id(query)

                if not reel_id:
                    output_data['api']['errorMessage'] = 'The URL provided does not contain a valid Instagram Reel ID.'
                    return output_data, 400

                def safe_unquote_url(url: str) -> str:
                    """
                    Safely unquote URL.
                    :param url: URL to be unquoted.
                    :return: Unquoted URL.
                    """

                    parsed_url = urlparse(url)
                    unquoted_url_base = unquote_plus(parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path)
                    return str(unquoted_url_base + '?' + urlencode(parse_qs(parsed_url.query), doseq=True))

                # Main process
                try:
                    instaloader = Instaloader()
                    post_data = instagram_post.from_shortcode(instaloader.context, reel_id)
                except Exception:
                    output_data['api']['errorMessage'] = 'Some error occurred while scraping the Instagram Reels URL. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                filename = format_string(post_data.owner_username + '_' + reel_id + '.mp4')
                media_url = safe_unquote_url(post_data.video_url)
                thumbnail_url = safe_unquote_url(post_data.url)

                timer.stop()

                output_data['response'] = {'filename': filename, 'mediaUrl': media_url, 'thumbnailUrl': thumbnail_url}
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class scrap_tiktok_video:
            ready_to_production = True

            endpoint_url = 'scrap-tiktok-video'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=60, per_day=500000)
            cache_timeout = 43200

            title = 'TikTok Video URL Scraper'
            description = 'Scrapes TikTok video URL to get the media and thumbnail URLs.'
            parameters = {
                'query': {'description': 'TikTok video URL.', 'required': True, 'type': 'string'}
            }
            expected_output = {
                'filename': 'string',
                'mediaUrl': 'string',
                'thumbnailUrl': 'string'
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    query = request_data['args']['query']
                else:
                    output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                def is_valid_tiktok_url(query: str) -> bool:
                    pattern = re_compile(r'(https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+|https?://vm\.tiktok\.com/[\w\d]+)')
                    return bool(pattern.match(query))

                if not is_valid_tiktok_url(query):
                    output_data['api']['errorMessage'] = 'The URL provided is not a valid TikTok video URL.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                try:
                    temp_response = get('https://www.tiktok.com/oembed', params={'url': query}, headers={'User-Agent': fake.user_agent(), 'X-Forwarded-For': fake.ipv4_public()}, timeout=10)
                except HTTPError:
                    output_data['api']['errorMessage'] = 'Some error occurred in our systems during the data search. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                if not temp_response or not temp_response.json():
                    output_data['api']['errorMessage'] = 'Some external error occurred during the data lookup. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                response_data = temp_response.json()

                if response_data.get('type') != 'video':
                    output_data['api']['errorMessage'] = 'Only video URLs are supported for now.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                # Main process
                filename = format_string(response_data.get('title', 'tiktok_video')) + '.mp4'
                thumbnail_url = unquote(response_data.get('thumbnail_url', str()))

                try:
                    response = post('https://savetik.co/api/ajaxSearch', headers={'User-Agent': fake.user_agent(), 'X-Forwarded-For': fake.ipv4_public(), 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}, data={'q': query}, timeout=10)
                except HTTPError:
                    output_data['api']['errorMessage'] = 'Some error occurred in our systems during the data scraping. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                soup = BeautifulSoup(response.text, 'html.parser')
                found_urls = set(re_findall(r'https://[^/]+\.akamaized\.net/[^\s\"\'>]+', soup.prettify()))
                fixed_urls = {unquote(url.split('?')[0]) + f'?mime_type=video_mp4&filename={soup.find('h3').text.strip()}.mp4' for url in found_urls}

                media_url = next(iter(fixed_urls), None)

                timer.stop()

                output_data['response'] = {'filename': filename, 'thumbnailUrl': thumbnail_url, 'mediaUrl': media_url}
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class scrap_youtube_video:
            ready_to_production = True

            endpoint_url = 'scrap-youtube-video'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=60, per_day=500000)
            cache_timeout = 3600

            title = 'YouTube Video URL Scraper'
            description = 'Scrapes YouTube video URL to get all the available information about the video.'
            parameters = {
                'query': {'description': 'YouTube video URL.', 'required': True, 'type': 'string'}
            }
            expected_output = {
                'info': {
                    'availability': 'string',
                    'categories': 'list',
                    'channelId': 'string',
                    'channelName': 'string',
                    'channelUrl': 'string',
                    'chapters': 'list',
                    'cleanChannelName': 'string',
                    'cleanTitle': 'string',
                    'commentCount': 'integer',
                    'description': 'string',
                    'duration': 'integer',
                    'embedUrl': 'string',
                    'followCount': 'integer',
                    'fullUrl': 'string',
                    'id': 'string',
                    'isAgeRestricted': 'boolean',
                    'isStreaming': 'boolean',
                    'isVerifiedChannel': 'boolean',
                    'language': 'string',
                    'likeCount': 'integer',
                    'shortUrl': 'string',
                    'tags': 'list',
                    'thumbnails': 'list',
                    'title': 'string',
                    'uploadTimestamp': 'integer',
                    'viewCount': 'integer'
                },
                'media': {
                    'audio': [
                        {
                            'bitrate': 'float',
                            'channels': 'integer',
                            'codec': 'string',
                            'codecVariant': 'string',
                            'extension': 'string',
                            'language': 'string',
                            'qualityNote': 'string',
                            'rawCodec': 'string',
                            'samplerate': 'integer',
                            'size': 'integer',
                            'url': 'string',
                            'youtubeFormatId': 'integer'
                        }
                    ],
                    'subtitle': {
                        'string': [
                            {
                                'extension': 'string',
                                'language': 'string',
                                'url': 'string'
                            }
                        ]
                    },
                    'video': [
                        {
                            'bitrate': 'float',
                            'codec': 'string',
                            'codecVariant': 'string',
                            'extension': 'string',
                            'framerate': 'integer',
                            'height': 'integer',
                            'language': 'string',
                            'quality': 'integer',
                            'qualityNote': 'string',
                            'rawCodec': 'string',
                            'size': 'integer',
                            'url': 'string',
                            'width': 'integer',
                            'youtubeFormatId': 'integer'
                        }
                    ]
                }
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    query = request_data['args']['query']
                else:
                    output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                def parse_youtube_url(query: str) -> Dict[str, Optional[Union[bool, str]]]:
                    """
                    Parse YouTube URL to get video and/or playlist ID.
                    :param query: YouTube URL.
                    :return: Dictionary with success status, URL type, video ID, and playlist ID.
                    """

                    result_data = {'status': False, 'urlType': None, 'videoId': None, 'playlistId': None}

                    video_regex = r'(?:(?:youtube\.com\/(?:[^\/\n\s?]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]+))'
                    playlist_regex = r'(?:list=)([a-zA-Z0-9_-]+)'

                    video_match = re_search(video_regex, query)
                    playlist_match = re_search(playlist_regex, query)
                    valid_domain = 'youtube.com' in query or 'youtu.be' in query

                    if valid_domain:
                        if video_match:
                            result_data['status'] = True
                            result_data['urlType'] = 'video'
                            result_data['videoId'] = video_match.group(1)

                            if playlist_match:
                                result_data['playlistId'] = playlist_match.group(1)
                        elif playlist_match:
                            result_data['status'] = True
                            result_data['urlType'] = 'playlist'
                            result_data['playlistId'] = playlist_match.group(1)

                    return result_data

                parsed_url_data = parse_youtube_url(query)
                if not parsed_url_data['status']:
                    output_data['api']['errorMessage'] = 'The URL provided is not a valid YouTube video URL.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400
                elif parsed_url_data['urlType'] != 'video':
                    output_data['api']['errorMessage'] = 'Only video URLs are supported for now.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                # Main process
                class DLPHumanizer:
                    """
                    A class to extract and format data from YouTube videos using yt-dlp.
                    """

                    def __init__(self, url: str, quiet: bool = False, no_warnings: bool = True, ignore_errors: bool = True) -> None:
                        """
                        Initialize the DLPHumanizer class.
                        :param url: The YouTube video url to extract data from.
                        :param quiet: Whether to suppress console output from yt-dlp.
                        :param no_warnings: Whether to suppress warnings from yt-dlp.
                        :param ignore_errors: Whether to ignore errors from yt-dlp.
                        """

                        self._ydl_opts: Dict[str, bool] = {
                            'extract_flat': True,
                            'geo_bypass': True,
                            'noplaylist': True,
                            'age_limit': None,
                            'quiet': quiet,
                            'no_warnings': no_warnings,
                            'ignoreerrors': ignore_errors
                        }

                        self._url: str = url
                        self._raw_youtube_data: Dict[Any, Any] = {}
                        self._raw_youtube_streams: List[Dict[Any, Any]] = []
                        self._raw_youtube_subtitles: Dict[str, List[Dict[str, str]]] = {}

                        self.media_info: Dict[str, Any] = {}

                        self.best_video_streams: Optional[List[Dict[str, Any]]] = []
                        self.best_video_stream: Optional[Dict[str, Any]] = {}
                        self.best_video_download_url: Optional[str] = None

                        self.best_audio_streams: Optional[List[Dict[str, Any]]] = []
                        self.best_audio_stream: Optional[Dict[str, Any]] = {}
                        self.best_audio_download_url: Optional[str] = None

                        self.subtitle_streams: Dict[str, List[Dict[str, str]]] = {}

                    def extract(self, source_data: Dict[Any, Any] = None) -> Optional[False]:
                        """
                        Extracts all the source data from the media using yt-dlp.
                        :param source_data: The source data you extracted using yt-dlp.
                        """

                        if source_data:
                            self._raw_youtube_data = source_data
                            self._raw_youtube_streams = source_data.get('formats', [])
                            self._raw_youtube_subtitles = source_data.get('subtitles', {})
                        else:
                            try:
                                with YoutubeDL(self._ydl_opts) as ydl:
                                    self._raw_youtube_data = dict(ydl.extract_info(self._url, download=False, process=True))
                            except (Exception, YTDLPDownloadError):
                                return False

                            self._raw_youtube_streams = self._raw_youtube_data.get('formats', [])
                            self._raw_youtube_subtitles = self._raw_youtube_data.get('subtitles', {})

                    def retrieve_media_info(self) -> None:
                        """
                        Extract and format relevant information from the raw yt-dlp response.
                        :return: The formatted media information if return_data is True, else None.
                        """

                        data = self._raw_youtube_data

                        id_ = data.get('id')
                        title = get_value(data, 'fulltitle', 'title')
                        clean_title = format_string(title)
                        channel_name = get_value(data, 'channel', 'uploader')
                        clean_channel_name = format_string(channel_name)
                        chapters = data.get('chapters', [])

                        if chapters:
                            chapters = [
                                {
                                    'title': chapter.get('title'),
                                    'startTime': get_value(chapter, 'start_time', convert_to=float),
                                    'endTime': get_value(chapter, 'end_time', convert_to=float)
                                }
                                for chapter in chapters
                            ]

                        media_info = {
                            'fullUrl': f'https://www.youtube.com/watch?v={id_}',
                            'shortUrl': f'https://youtu.be/{id_}',
                            'embedUrl': f'https://www.youtube.com/embed/{id_}',
                            'id': id_,
                            'title': title,
                            'cleanTitle': clean_title,
                            'description': data.get('description'),
                            'channelId': data.get('channel_id'),
                            'channelUrl': get_value(data, 'uploader_url', 'channel_url'),
                            'channelName': channel_name,
                            'cleanChannelName': clean_channel_name,
                            'isVerifiedChannel': get_value(data, 'channel_is_verified', default_to=False),
                            'duration': get_value(data, 'duration'),
                            'viewCount': get_value(data, 'view_count'),
                            'isAgeRestricted': get_value(data, 'age_limit', convert_to=bool),
                            'categories': get_value(data, 'categories', default_to=[]),
                            'tags': get_value(data, 'tags', default_to=[]),
                            'isStreaming': get_value(data, 'is_live'),
                            'uploadTimestamp': get_value(data, 'timestamp', 'release_timestamp'),
                            'availability': get_value(data, 'availability'),
                            'chapters': chapters,
                            'commentCount': get_value(data, 'comment_count'),
                            'likeCount': get_value(data, 'like_count'),
                            'followCount': get_value(data, 'channel_follower_count'),
                            'language': get_value(data, 'language'),
                            'thumbnails': [
                                f'https://img.youtube.com/vi/{id_}/maxresdefault.jpg',
                                f'https://img.youtube.com/vi/{id_}/sddefault.jpg',
                                f'https://img.youtube.com/vi/{id_}/hqdefault.jpg',
                                f'https://img.youtube.com/vi/{id_}/mqdefault.jpg',
                                f'https://img.youtube.com/vi/{id_}/default.jpg'
                            ]
                        }

                        self.media_info = dict(sorted(media_info.items()))

                    def analyze_video_streams(self) -> None:
                        """
                        Extract and format the best video streams from the raw yt-dlp response.
                        :return: The formatted video streams if return_data is True, else None.
                        """

                        data = self._raw_youtube_streams

                        format_id_extension_map = {
                            702: 'mp4', 571: 'mp4', 402: 'mp4', 272: 'webm',  # 7680x4320
                            701: 'mp4', 401: 'mp4', 337: 'webm', 315: 'webm', 313: 'webm', 305: 'mp4', 266: 'mp4',  # 3840x2160
                            700: 'mp4', 400: 'mp4', 336: 'webm', 308: 'webm', 271: 'webm', 304: 'mp4', 264: 'mp4',  # 2560x1440
                            699: 'mp4', 399: 'mp4', 335: 'webm', 303: 'webm', 248: 'webm', 299: 'mp4', 137: 'mp4', 216: 'mp4', 170: 'webm',  # 1920x1080 (616: 'webm' - Premium [m3u8])
                            698: 'mp4', 398: 'mp4', 334: 'webm', 302: 'webm', 612: 'webm', 247: 'webm', 298: 'mp4', 136: 'mp4', 169: 'webm',  # 1280x720
                            697: 'mp4', 397: 'mp4', 333: 'webm', 244: 'webm', 135: 'mp4', 168: 'webm',  # 854x480
                            696: 'mp4', 396: 'mp4', 332: 'webm', 243: 'webm', 134: 'mp4', 167: 'webm',  # 640x360
                            695: 'mp4', 395: 'mp4', 331: 'webm', 242: 'webm', 133: 'mp4',  # 426x240
                            694: 'mp4', 394: 'mp4', 330: 'webm', 278: 'webm', 598: 'webm', 160: 'mp4', 597: 'mp4',  # 256x144
                        }

                        video_streams = [
                            stream for stream in data
                            if stream.get('vcodec') != 'none' and int(get_value(stream, 'format_id').split('-')[0]) in format_id_extension_map
                        ]

                        def calculate_score(stream: Dict[Any, Any]) -> float:
                            width = stream.get('width', 0)
                            height = stream.get('height', 0)
                            framerate = stream.get('fps', 0)
                            bitrate = stream.get('tbr', 0)

                            return width * height * framerate * bitrate

                        sorted_video_streams = sorted(video_streams, key=calculate_score, reverse=True)

                        def extract_stream_info(stream: Dict[Any, Any]) -> Dict[str, Any]:
                            codec = stream.get('vcodec', '')
                            codec_parts = codec.split('.', 1)
                            youtube_format_id = int(get_value(stream, 'format_id').split('-')[0])

                            return {
                                'url': stream.get('url'),
                                'codec': codec_parts[0] if codec_parts else None,
                                'codecVariant': codec_parts[1] if len(codec_parts) > 1 else None,
                                'rawCodec': codec,
                                'extension': format_id_extension_map.get(youtube_format_id, 'mp3'),
                                'width': stream.get('width'),
                                'height': stream.get('height'),
                                'framerate': stream.get('fps'),
                                'bitrate': stream.get('tbr'),
                                'quality': stream.get('height'),
                                'qualityNote': stream.get('format_note'),
                                'size': stream.get('filesize'),
                                'language': stream.get('language'),
                                'youtubeFormatId': youtube_format_id
                            }

                        self.best_video_streams = [extract_stream_info(stream) for stream in sorted_video_streams] if sorted_video_streams else None
                        self.best_video_stream = self.best_video_streams[0] if self.best_video_streams else None
                        self.best_video_download_url = self.best_video_stream['url'] if self.best_video_stream else None

                    def analyze_audio_streams(self) -> None:
                        """
                        Extract and format the best audio streams from the raw yt-dlp response.
                        :return: The formatted audio streams if return_data is True, else None.
                        """

                        data = self._raw_youtube_streams

                        format_id_extension_map = {
                            338: 'webm',  # Opus - (VBR) ~480 Kbps (?) - Quadraphonic (4)
                            380: 'mp4',  # AC3 - 384 Kbps - Surround (5.1) - Rarely
                            328: 'mp4',  # EAC3 - 384 Kbps - Surround (5.1) - Rarely
                            258: 'mp4',  # AAC (LC) - 384 Kbps - Surround (5.1) - Rarely
                            325: 'mp4',  # DTSE (DTS Express) - 384 Kbps - Surround (5.1) - Rarely*
                            327: 'mp4',  # AAC (LC) - 256 Kbps - Surround (5.1) - ?*
                            141: 'mp4',  # AAC (LC) - 256 Kbps - Stereo (2) - No, YT Music*
                            774: 'webm',  # Opus - (VBR) ~256 Kbps - Stereo (2) - Some, YT Music*
                            256: 'mp4',  # AAC (HE v1) - 192 Kbps - Surround (5.1) - Rarely
                            251: 'webm',  # Opus - (VBR) <=160 Kbps - Stereo (2) - Yes
                            140: 'mp4',  # AAC (LC) - 128 Kbps - Stereo (2) - Yes, YT Music
                            250: 'webm',  # Opus - (VBR) ~70 Kbps - Stereo (2) - Yes
                            249: 'webm',  # Opus - (VBR) ~50 Kbps - Stereo (2) - Yes
                            139: 'mp4',  # AAC (HE v1) - 48 Kbps - Stereo (2) - Yes, YT Music
                            600: 'webm',  # Opus - (VBR) ~35 Kbps - Stereo (2) - Yes
                            599: 'mp4',  # AAC (HE v1) - 30 Kbps - Stereo (2) - Yes
                        }

                        audio_streams = [
                            stream for stream in data
                            if stream.get('acodec') != 'none' and int(get_value(stream, 'format_id').split('-')[0]) in format_id_extension_map
                        ]

                        def calculate_score(stream: Dict[Any, Any]) -> float:
                            bitrate = stream.get('abr', 0)
                            sample_rate = stream.get('asr', 0)

                            return bitrate * 1.5 + sample_rate / 1000

                        sorted_audio_streams = sorted(audio_streams, key=calculate_score, reverse=True)

                        def extract_stream_info(stream: Dict[Any, Any]) -> Dict[str, Any]:
                            codec = stream.get('acodec', '')
                            codec_parts = codec.split('.', 1)
                            youtube_format_id = int(get_value(stream, 'format_id').split('-')[0])

                            return {
                                'url': stream.get('url'),
                                'codec': codec_parts[0] if codec_parts else None,
                                'codecVariant': codec_parts[1] if len(codec_parts) > 1 else None,
                                'rawCodec': codec,
                                'extension': format_id_extension_map.get(youtube_format_id, 'mp3'),
                                'bitrate': stream.get('abr'),
                                'qualityNote': stream.get('format_note'),
                                'size': stream.get('filesize'),
                                'samplerate': stream.get('asr'),
                                'channels': stream.get('audio_channels'),
                                'language': stream.get('language'),
                                'youtubeFormatId': youtube_format_id
                            }

                        self.best_audio_streams = [extract_stream_info(stream) for stream in sorted_audio_streams] if sorted_audio_streams else None
                        self.best_audio_stream = self.best_audio_streams[0] if self.best_audio_streams else None
                        self.best_audio_download_url = self.best_audio_stream['url'] if self.best_audio_stream else None

                    def analyze_subtitle_streams(self) -> None:
                        """
                        Extract and format the best subtitle streams from the raw yt-dlp response.
                        :return: The formatted subtitle streams if return_data is True, else None.
                        """

                        data = self._raw_youtube_subtitles

                        subtitle_streams = {}

                        for stream in data:
                            subtitle_streams[stream] = [
                                {
                                    'extension': subtitle.get('ext'),
                                    'url': subtitle.get('url'),
                                    'language': subtitle.get('name')
                                }
                                for subtitle in data[stream]
                            ]

                        self.subtitle_streams = dict(sorted(subtitle_streams.items()))

                    # @staticmethod
                    # def save_json(path: Union[AnyStr, Path, PathLike], data: Union[Dict[Any, Any], List[Any]], indent_code: bool = True) -> None:
                    #     """
                    #     Save a dictionary/list to a JSON file.
                    #     :param path: The path to save the JSON file to.
                    #     :param data: The dictionary/list to save to the JSON file.
                    #     :param indent_code: Whether to indent the JSON code. (2 spaces)
                    #     """
                    #
                    #     Path(path).write_bytes(orjson_dumps(data, option=OPT_INDENT_2 if indent_code else None))

                dlp_humanizer = DLPHumanizer(query, quiet=True)
                download_status = dlp_humanizer.extract()

                if download_status is False:
                    output_data['api']['errorMessage'] = 'Some error occurred while extracting the video data. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                dlp_humanizer.retrieve_media_info()
                dlp_humanizer.analyze_video_streams()
                dlp_humanizer.analyze_audio_streams()
                dlp_humanizer.analyze_subtitle_streams()

                formatted_data = {
                    'info': dlp_humanizer.media_info,
                    'media': {
                        'video': dlp_humanizer.best_video_streams,
                        'audio': dlp_humanizer.best_audio_streams,
                        'subtitle': dlp_humanizer.subtitle_streams
                    }
                }

                timer.stop()

                output_data['response'] = formatted_data
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class scrap_youtube_search_results:
            ready_to_production = True

            endpoint_url = 'scrap-youtube-search-results'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=4, per_min=120, per_day=500000)
            cache_timeout = 3600

            title = 'YouTube Search Results Scraper'
            description = 'Scrapes YouTube search results and returns a list of extracted videos.'
            parameters = {
                'query': {'description': 'Search query.', 'required': True, 'type': 'string'}
            }
            expected_output = {
                'extractedUrlsData': [
                    {
                        'channelId': 'string',
                        'channelName': 'string',
                        'channelUrl': 'string',
                        'duration': 'integer',
                        'thumbnailUrls': 'list',
                        'videoId': 'string',
                        'videoTitle': 'string',
                        'videoUrl': 'string',
                        'viewCount': 'integer'
                    }
                ]
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    query = str(request_data['args']['query']).strip()

                    if not query:
                        output_data['api']['errorMessage'] = 'The "query" parameter must not be empty.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 400
                else:
                    output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                # Main process
                params = {'search_query': query}
                headers = {'User-Agent': fake.user_agent(), 'X-Forwarded-For': fake.ipv4_public(), 'Accept': 'text/html'}

                try:
                    response = get('https://www.youtube.com/results', params=params, headers=headers, timeout=10)
                    response.raise_for_status()
                except HTTPError:
                    output_data['api']['errorMessage'] = 'Some error occurred while fetching the search results. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                if response.status_code != 200:
                    output_data['api']['errorMessage'] = 'Some error occurred in our systems during the data scraping. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                try:
                    tree = html.fromstring(response.text)
                    script = tree.xpath('//script[contains(text(), "ytInitialData")]/text()')
                    script_content = re_search(r'var ytInitialData = ({.*?});', script[0])
                except (AttributeError, IndexError, KeyError):
                    output_data['api']['errorMessage'] = 'No video data found in the URL provided.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                try:
                    json_data = orjson_loads(script_content.group(1))['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
                    json_data = [i['videoRenderer'] for i in json_data if 'videoRenderer' in i]
                except (AttributeError, IndexError, KeyError):
                    output_data['api']['errorMessage'] = 'No video data found in the URL provided.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                scraped_data = []

                for data in json_data:
                    video_id = str(data.get('videoId'))

                    if not video_id:
                        continue

                    title = str(data.get('title', {}).get('runs', [{}])[0].get('text', None))
                    duration = int(sum(int(x) * 60 ** i for i, x in enumerate(reversed(data.get('lengthText', {}).get('simpleText').split(':')))))
                    channel_id = str(data.get('ownerText', {}).get('runs', [{}])[0].get('navigationEndpoint', {}).get('browseEndpoint', {}).get('browseId', None))
                    channel_url = f'https://www.youtube.com/channel/{channel_id}'
                    channel_name = str(data.get('ownerText', {}).get('runs', [{}])[0].get('text', None))
                    view_count = data.get('viewCountText', {}).get('simpleText', '0').split()[0].replace('.', '')

                    scraped_data.append({
                        'channelId': channel_id,
                        'channelName': channel_name,
                        'channelUrl': channel_url,
                        'duration': duration,
                        'thumbnailUrls': [f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg', f'https://img.youtube.com/vi/{video_id}/sddefault.jpg', f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg', f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg', f'https://img.youtube.com/vi/{video_id}/default.jpg'],
                        'videoId': video_id,
                        'videoTitle': title,
                        'videoUrl': f'https://www.youtube.com/watch?v={video_id}',
                        'viewCount': view_count,
                    })

                if not scraped_data:
                    output_data['api']['errorMessage'] = 'No video data found in the URL provided.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                timer.stop()

                output_data['response'] = {'extractedUrlsData': scraped_data}
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class scrap_soundcloud_track:
            ready_to_production = True

            endpoint_url = 'scrap-soundcloud-track'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=60, per_day=500000)
            cache_timeout = 3600

            title = 'SoundCloud Track URL Scraper'
            description = 'Scrapes SoundCloud track URL to get the media and thumbnail URLs.'
            parameters = {
                'query': {'description': 'SoundCloud track URL.', 'required': True, 'type': 'string'}
            }
            expected_output = {
                'filename': 'string',
                'mediaUrl': 'string',
                'thumbnailUrl': 'string'
            }

            @staticmethod
            def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                timer = APITools.Timer()
                output_data = APITools.get_default_api_output_dict()

                api_request_id = db_client.start_request(request_data, timer.start_time)

                # Request data validation
                if request_data['args'].get('query'):
                    query = request_data['args']['query']
                else:
                    output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                def is_valid_soundcloud_url(query: str) -> bool:
                    pattern = re_compile(r'^https?://soundcloud\.com/[\w-]+/[\w-]+(\?.*)?$')
                    return bool(pattern.match(query))

                if not is_valid_soundcloud_url(query):
                    output_data['api']['errorMessage'] = 'The URL provided is not a valid SoundCloud music URL.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                # Main process
                try:
                    soundcloud_api = SoundcloudAPI()
                    track_data = soundcloud_api.resolve(query)
                    if not isinstance(track_data, SoundcloudTrack): raise Exception
                except (Exception, TypeError):
                    output_data['api']['errorMessage'] = 'Some error occurred while scraping the SoundCloud track URL. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                try:
                    media_url = unquote(orjson_loads(get(track_data.get_prog_url(), headers={'User-Agent': fake.user_agent(), 'X-Forwarded-For': fake.ipv4_public()}, timeout=10).content)['url'])
                except (JSONDecodeError, HTTPError, KeyError):
                    output_data['api']['errorMessage'] = 'Some error occurred while fetching the media URL. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                filename = format_string(f'{track_data.title} - {track_data.artist}') + '.mp3'
                thumbnail_url = unquote(track_data.artwork_url.replace('-large.', '-original.'))

                timer.stop()

                output_data['response'] = {'filename': filename, 'mediaUrl': media_url, 'thumbnailUrl': thumbnail_url}
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200
