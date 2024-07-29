# Built-in modules
from collections import Counter
from datetime import datetime
from re import compile as re_compile, sub as re_sub, findall as re_findall, search as re_search, match as re_match
from subprocess import run as run_subprocess, CalledProcessError as SubprocessCalledProcessError
from typing import Any, AnyStr, Optional, Union, List, Dict, Tuple
from urllib.parse import urlparse, parse_qs, unquote, urlencode, unquote_plus

# Third-party modules
from bs4 import BeautifulSoup
from faker import Faker
from googlesearch import search as google_search
from googletrans import Translator
from httpx import get, post, HTTPError
from instaloader import Instaloader, Post as instagram_post
from langdetect import detect as lang_detect, DetectorFactory, LangDetectException
from lxml import html
from orjson import loads as orjson_loads
from psycopg2 import connect as psycopg2_connect
from sclib import SoundcloudAPI, Track as SoundcloudTrack
from unicodedata import normalize
from user_agents import parse as UserAgentParser
from yt_dlp import YoutubeDL

# Local modules
from static.data.functions import APITools, LimiterTools


# Global variables
fake = Faker()

# Helper functions
def format_string(query: AnyStr, max_length: int = 128) -> str:
    """
    Format string to remove special characters and normalize it.
    :param query: String to be sanitized.
    :param max_length: Maximum length of the string (if exceeds, it will be truncated).
    :return: Sanitized string.
    """

    # Normalize string, remove special characters and extra spaces
    normalized_string = str(normalize('NFKD', query).encode('ASCII', 'ignore').decode('utf-8')).strip()
    sanitized_string = str(re_sub(r'\s+', ' ', re_sub(r'[^a-zA-Z0-9\-_()[\]{}!$#+,. ]', str(), normalized_string)).strip())

    # Truncate string if it exceeds the maximum length
    if len(sanitized_string) > max_length: sanitized_string = str(sanitized_string[:max_length].rsplit(' ', 1)[0])

    # Return the sanitized string
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

        class useragent_parser:
            ready_to_production = True

            endpoint_url = 'useragent-parser'
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

                timer.stop()

                output_data['response'] = parsed_ua_data
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class url_parser:
            ready_to_production = True

            endpoint_url = 'url-parser'
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

        class email_parser:
            ready_to_production = True

            endpoint_url = 'email-parser'
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

                timer.stop()

                output_data['response'] = parsed_email_data
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class advanced_text_counter:
            ready_to_production = True

            endpoint_url = 'advanced-text-counter'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=5, per_min=300, per_day=1000000)
            cache_timeout = 1

            title = 'Advanced Text Counter'
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

        class text_language_detector:
            ready_to_production = True

            endpoint_url = 'text-language-detector'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=4, per_min=120, per_day=500000)
            cache_timeout = 300

            title = 'Text Language Detector'
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
                DetectorFactory.seed = 0

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

        class text_translator:
            ready_to_production = True

            endpoint_url = 'text-translator'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=120, per_day=500000)
            cache_timeout = 300

            title = 'Text Translator'
            description = 'Translate text from one language to another.'
            parameters = {
                'query': {'description': 'Text to be translated.', 'required': True, 'type': 'string'},
                'src_lang': {'description': 'Source language code (e.g., "pt" for Portuguese). If not provided, the language will be automatically detected.', 'required': False, 'type': 'string'},
                'dest_lang': {'description': 'Destination language code (e.g., "en" for English).', 'required': True, 'type': 'string'}
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

                if request_data['args'].get('dest_lang'):
                    dest_lang = str(request_data['args']['dest_lang']).replace('-', '_')
                else:
                    output_data['api']['errorMessage'] = 'No "dest_lang" parameter found in the request.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                src_lang = request_data['args'].get('src_lang', None)

                # Main process
                try:
                    translator = Translator()
                    translated_text = translator.translate(text, src='auto' if not src_lang else str(src_lang).replace('-', '_'), dest=dest_lang)
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

        class my_ip:
            ready_to_production = True

            endpoint_url = 'my-ip'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=4, per_min=120, per_day=500000)
            cache_timeout = 1

            title = 'My IP Address'
            description = 'Get your IP address.'
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

        class get_latest_ffmpeg_download_url:
            ready_to_production = True

            endpoint_url = 'get-latest-ffmpeg-download-url'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=60, per_day=500000)
            cache_timeout = 3600

            title = 'Retrieve Latest FFmpeg Download URL'
            description = 'Get the download url of the latest FFmpeg build according to your specifications.'
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
                    response = get('https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest', timeout=10)
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

        class ffprobe_a_video_url:
            ready_to_production = True

            endpoint_url = 'ffprobe-a-video-url'
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
                except SubprocessCalledProcessError as e:
                    output_data['api']['errorMessage'] = 'Some error occurred while running the FFprobe command. Please use a valid video URL.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500
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
            cache_timeout = 300

            title = 'Google Search Results Scraper'
            description = 'Scrapes Google search results for a given query.'
            parameters = {
                'query': {'description': 'Search query.', 'required': True, 'type': 'string'},
                'max_results': {'description': 'Maximum number of results to be returned (default: 10, min: 1, max: 50).', 'required': False, 'type': 'integer'}
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

                max_results = request_data['args'].get('max_results', 10)
                if not max_results: max_results = 10

                try:
                    max_results = int(max_results)

                    if max_results < 1:
                        output_data['api']['errorMessage'] = 'The "max_results" parameter must be greater than 0.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 400
                    elif max_results > 50:
                        output_data['api']['errorMessage'] = 'The "max_results" parameter must be less than or equal to 50.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 400
                except ValueError:
                    output_data['api']['errorMessage'] = 'The "max_results" parameter must be an integer.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                # Main process
                scraped_results = list()
                search_results = list()

                try:
                    scraped_results = google_search(query, num_results=max_results, lang='en')
                except Exception:
                    output_data['api']['errorMessage'] = 'Some error occurred while scraping the search results. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())

                for result in scraped_results:
                    search_results.append(unquote(result))

                search_results = list(set(search_results))

                timer.stop()

                output_data['response'] = {'searchResults': search_results}
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class scrap_instagram_reel_url:
            ready_to_production = False

            endpoint_url = 'scrap-instagram-reel-url'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=60, per_day=500000)
            cache_timeout = 3600

            title = 'Instagram Reel URL Scraper'
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

                    pattern = re_compile(r'^(https?://)?(www\.)?instagram\.com(/[^/]+)?/(reel|p)/[A-Za-z0-9_-]+/?(\?.*)?$')
                    return bool(pattern.match(query))

                def extract_instagram_reel_id(query: str) -> Optional[str]:
                    """
                    Extract the ID from a valid Instagram Reels URL.
                    :param query: URL to be checked.
                    :return: The ID of the Instagram Reel if the URL is valid, None otherwise.
                    """

                    pattern = re_compile(r'^(https?://)?(www\.)?instagram\.com(/[^/]+)?/(reel|p)/([A-Za-z0-9_-]+)/?(\?.*)?$')
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

        class scrap_tiktok_video_url:
            ready_to_production = True

            endpoint_url = 'scrap-tiktok-video-url'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=60, per_day=500000)
            cache_timeout = 3600

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
                    temp_response = get('https://www.tiktok.com/oembed', params={'url': query}, headers={'User-Agent': fake.user_agent()}, timeout=10)
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
                    response = post('https://savetik.co/api/ajaxSearch', headers={'User-Agent': fake.user_agent(), 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}, data={'q': query}, timeout=10)
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

        class scrap_youtube_video_url:
            ready_to_production = True

            endpoint_url = 'scrap-youtube-video-url'
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
                    'channelId': 'string',
                    'channelName': 'string',
                    'channelUrl': 'string',
                    'commentCount': 'integer',
                    'formattedChannelName': 'string',
                    'formattedMediaDurationTime': 'string',
                    'formattedMediaTitle': 'string',
                    'likeCount': 'integer',
                    'mediaCategories': 'list',
                    'mediaDescription': 'string',
                    'mediaDurationTime': 'integer',
                    'mediaEmbedUrl': 'string',
                    'mediaId': 'string',
                    'mediaIsAgeRestringicted': 'boolean',
                    'mediaIsstringeaming': 'boolean',
                    'mediaShortUrl': 'string',
                    'mediaTags': 'list',
                    'mediaTitle': 'string',
                    'mediaUploadedAt': 'integer',
                    'mediaUrl': 'string',
                    'viewCount': 'integer'
                },
                'media': {
                    'audio': {
                        'bitrate': 'integer',
                        'codec': 'string',
                        'samplerate': 'integer',
                        'size': 'integer',
                        'url': 'string'
                    },
                    'subtitle': [
                        {
                            'ext': 'string',
                            'lang': 'string',
                            'url': 'string'
                        }
                    ],
                    'video': {
                        'bitrate': 'integer',
                        'codec': 'string',
                        'framerate': 'integer',
                        'quality': 'integer',
                        'url': 'string'
                    }
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
                def extract_media_info(data: dict) -> Dict[str, Any]:
                    # Media information
                    media_id = str(data.get('id', str()))
                    media_title = str(data.get('title', str()))
                    media_formatted_title = format_string(media_title)
                    media_description = str(data.get('description', str()))
                    media_uploaded_at = int(datetime.strptime(str(data.get('upload_date', '0')), '%Y%m%d').timestamp())
                    media_duration_time = int(data.get('duration', 0))
                    media_formatted_duration_time = str('{:02d}:{:02d}:{:02d}'.format(media_duration_time // 3600, (media_duration_time % 3600) // 60, media_duration_time % 60) if media_duration_time < 360000 else '{:d}:{:02d}:{:02d}'.format(media_duration_time // 3600, (media_duration_time % 3600) // 60, media_duration_time % 60))
                    media_categories = list(data.get('categories', list()))
                    media_tags = list(data.get('tags', list()))
                    view_count = int(data.get('view_count', 0))
                    like_count = int(data.get('like_count', 0))
                    comment_count = int(data.get('comment_count', 0))
                    media_is_streaming = bool(data.get('is_live', False))
                    media_is_age_restricted = bool(data.get('age_limit', False))

                    # URLs
                    media_url = f'https://www.youtube.com/watch?v={media_id}'
                    media_short_url = f'https://youtu.be/{media_id}'
                    media_embed_url = f'https://www.youtube.com/embed/{media_id}'

                    # Channel information
                    channel_id = data.get('channel_id', str())
                    channel_url = f'https://www.youtube.com/channel/{channel_id}' if channel_id else str()
                    channel_name = str(data.get('uploader', str()))
                    formatted_channel_name = format_string(channel_name)

                    return {
                        'mediaId': media_id, 'mediaTitle': media_title,
                        'formattedMediaTitle': media_formatted_title,
                        'mediaDescription': media_description,
                        'mediaUploadedAt': media_uploaded_at,
                        'mediaDurationTime': media_duration_time,
                        'formattedMediaDurationTime': media_formatted_duration_time,
                        'mediaCategories': media_categories,
                        'mediaTags': media_tags,
                        'viewCount': view_count,
                        'likeCount': like_count,
                        'commentCount': comment_count,
                        'mediaIsStreaming': media_is_streaming,
                        'mediaIsAgeRestricted': media_is_age_restricted,
                        'mediaUrl': media_url,
                        'mediaShortUrl': media_short_url,
                        'mediaEmbedUrl': media_embed_url,
                        'channelId': channel_id,
                        'channelUrl': channel_url,
                        'channelName': channel_name,
                        'formattedChannelName': formatted_channel_name
                    }

                def extract_media_subtitles(data: dict) -> List[Dict[str, str]]:
                    subtitles_data = data.get('subtitles', dict())
                    output_subtitle_info = list()

                    for lang, subs in subtitles_data.items():
                        for sub_info in subs:
                            subtitle_data = {'url': str(unquote(sub_info.get('url', str()))), 'lang': str(lang), 'ext': str(sub_info.get('ext', str()))}
                            output_subtitle_info.append(subtitle_data)

                    return output_subtitle_info

                def is_blacklisted_media_url(query: str) -> bool:
                    return not bool(re_match(r'https?://(?!manifest\.googlevideo\.com)\S+', query))

                def is_valid_video_data(data: Any) -> bool:
                    return data['vcodec'] != 'none' and not data.get('abr')

                def is_valid_audio_data(data: Any) -> bool:
                    return data.get('acodec', str()) != 'none'

                query_url = f'https://www.youtube.com/watch?v={parsed_url_data["videoId"]}'

                ydl_opts = {'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'quiet': True, 'no_warnings': True, 'ignoreerrors': True, 'geo_bypass': True}
                yt = YoutubeDL(ydl_opts)

                try:
                    raw_yt_extracted_data = yt.sanitize_info(yt.extract_info(query_url, download=False), remove_private_keys=True)
                    adjusted_yt_data = {'info': extract_media_info(raw_yt_extracted_data), 'media': {'video': list(), 'audio': list(), 'subtitle': list()}}
                except BaseException:
                    output_data['api']['errorMessage'] = 'The URL you have chosen does not exist or is temporarily unavailable.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 400

                yt_media_data = adjusted_yt_data['media']

                for format_data in raw_yt_extracted_data['formats']:
                    # Video data adjustment
                    if is_valid_video_data(format_data):
                        video_url = unquote(format_data.get('url', str()))

                        if not is_blacklisted_media_url(video_url):
                            size = format_data.get('filesize', None)

                            if size:
                                video_data = {'url': video_url, 'quality': int(format_data.get('height', 0)), 'codec': str(format_data.get('vcodec', str())).split('.')[0], 'framerate': int(format_data.get('fps', 0)), 'bitrate': int(format_data.get('tbr', 0))}
                                yt_media_data['video'].append(video_data)

                    # Audio data adjustment
                    if is_valid_audio_data(format_data):
                        audio_url = unquote(format_data.get('url', str()))

                        if not is_blacklisted_media_url(audio_url):
                            size = format_data.get('filesize', None)
                            bitrate = format_data.get('abr', None)

                            if size and bitrate:
                                audio_data = {'url': audio_url, 'codec': str(format_data.get('acodec', str())).split('.')[0], 'bitrate': int(bitrate), 'samplerate': int(format_data.get('asr', 0)), 'size': int(size)}
                                yt_media_data['audio'].append(audio_data)

                # Subtitle data adjustment
                yt_media_data['subtitle'] = extract_media_subtitles(raw_yt_extracted_data)

                timer.stop()

                output_data['response'] = adjusted_yt_data
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class get_youtube_video_url_from_search:
            ready_to_production = True

            endpoint_url = 'get-youtube-video-url-from-search'
            allowed_methods = ['GET']
            ratelimit = LimiterTools.gen_ratelimit_message(per_sec=4, per_min=120, per_day=500000)
            cache_timeout = 300

            title = 'Retrieve YouTube Video URL from Search'
            description = 'Get the YouTube video URL from a search query.'
            parameters = {
                'query': {'description': 'Search query.', 'required': True, 'type': 'string'}
            }
            expected_output = {
                'extractedUrlsData': [
                    {
                        'videoId': 'string',
                        'videoTitle': 'string',
                        'videoUrl': 'string',
                        'channelId': 'string',
                        'channelName': 'string',
                        'channelUrl': 'string',
                        'duration': 'integer',
                        'viewCount': 'integer',
                        'thumbnailUrls': 'list'
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
                headers = {'User-Agent': fake.user_agent(), 'X-Forwarded-For': fake.ipv4_public(), 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'}

                try:
                    response = get('https://www.youtube.com/results', params=params, headers=headers, timeout=10)
                    response.raise_for_status()
                except HTTPError:
                    output_data['api']['errorMessage'] = 'Some error occurred while fetching the search results. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                if response.status_code != 200:
                    output_data['api']['errorMessage'] = 'Some error occurred while fetching the search results. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                try:
                    tree = html.fromstring(response.text)
                    script = tree.xpath('//script[contains(text(), "ytInitialData")]/text()')
                    script_content = re_search(r'var ytInitialData = ({.*?});', script[0])
                except (IndexError, AttributeError):
                    output_data['api']['errorMessage'] = 'Some error occurred while parsing the search results. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                try:
                    json_data = orjson_loads(script_content.group(1))['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
                    json_data = [i['videoRenderer'] for i in json_data if 'videoRenderer' in i]
                except (IndexError, KeyError):
                    output_data['api']['errorMessage'] = 'No video data found in the search results.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 404

                scraped_data = list()

                for data in json_data:
                    video_id = str(data['videoId'])
                    title = str(data['title']['runs'][0]['text'])
                    channel_id = data['ownerText']['runs'][0]['navigationEndpoint']['browseEndpoint']['browseId']
                    channel_url = f'https://www.youtube.com/channel/{channel_id}'
                    channel_name = str(data['ownerText']['runs'][0]['text'])
                    duration = data.get('lengthText', {}).get('simpleText', None)
                    if duration: duration = int(sum(int(x) * 60 ** i for i, x in enumerate(reversed(duration.split(':')))))
                    view_count = int(data['viewCountText']['simpleText'].replace('.', '').replace(',', '').split()[0])
                    thumbnails_urls = [f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg', f'https://img.youtube.com/vi/{video_id}/sddefault.jpg', f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg', f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg', f'https://img.youtube.com/vi/{video_id}/default.jpg']

                    scraped_data.append({
                        'videoTitle': title,
                        'videoId': video_id,
                        'videoUrl': f'https://www.youtube.com/watch?v={video_id}',
                        'channelName': channel_name,
                        'channelId': channel_id,
                        'channelUrl': channel_url,
                        'duration': duration,
                        'viewCount': view_count,
                        'thumbnailUrls': thumbnails_urls
                    })

                timer.stop()

                output_data['response'] = {'extractedUrlsData': scraped_data}
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200

        class scrap_soundcloud_track_url:
            ready_to_production = True

            endpoint_url = 'scrap-soundcloud-track-url'
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
                    pattern = re_compile(r'^https?://soundcloud\.com/[\w-]+/[\w-]+$')
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
                except Exception:
                    output_data['api']['errorMessage'] = 'Some error occurred while scraping the SoundCloud track URL. Please try again later.'
                    db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                    return output_data, 500

                filename = format_string(f'{track_data.title} - {track_data.artist}') + '.mp3'
                media_url = unquote(track_data.get_stream_url())
                thumbnail_url = unquote(track_data.artwork_url.replace('-large', '-original'))

                timer.stop()

                output_data['response'] = {'filename': filename, 'mediaUrl': media_url, 'thumbnailUrl': thumbnail_url}
                output_data['api']['status'] = True
                output_data['api']['elapsedTime'] = timer.elapsed_time()

                db_client.update_request_status('success', api_request_id, timer.end_time)

                return output_data, 200
