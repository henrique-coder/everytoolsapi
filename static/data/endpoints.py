# Built-in modules
from collections import Counter
from datetime import datetime
from re import compile as re_compile, sub as re_sub, findall as re_findall, search as re_search, match as re_match
from subprocess import run as run_subprocess, CalledProcessError as SubprocessCalledProcessError
from typing import Any, AnyStr, Dict, Tuple, Optional, Union
from urllib.parse import urlparse, parse_qs, unquote, urlencode, unquote_plus

# Third-party modules
from bs4 import BeautifulSoup
from fake_useragent import FakeUserAgent
from googlesearch import search as google_search
from googletrans import Translator
from httpx import get, post, HTTPError
from langcodes import Language
from langdetect import detect as detect_lang, DetectorFactory, LangDetectException
from orjson import loads as orjson_loads
from psycopg2 import connect as psycopg2_connect
from unicodedata import normalize
from user_agents import parse as UserAgentParser
from youtubesearchpython import SearchVideos as SearchYouTubeVideos
from yt_dlp import YoutubeDL

# Local modules
from static.data.functions import APITools, LimiterTools


# Global variables/constants
fake_useragent = FakeUserAgent()

# Helper functions
def format_string(query: AnyStr, max_length: int = 128) -> str:
    """
    Format string to remove special characters and normalize it.
    :param query: String to be sanitized.
    :param max_length: Maximum length of the string (if exceeds, it will be truncated).
    :return: Sanitized string.
    """

    # Normalize string and remove special characters
    normalized_string = str(normalize('NFKD', query).encode('ASCII', 'ignore').decode('utf-8')).strip()

    # Remove extra spaces and special characters
    sanitized_string = str(re_sub(r'\s+', ' ', re_sub(r'[^a-zA-Z0-9\-_()[\]{}!$#+,. ]', str(), normalized_string)).strip())

    # Truncate string if it exceeds the maximum length
    if len(sanitized_string) > max_length: sanitized_string = str(sanitized_string[:max_length].rsplit(' ', 1)[0])

    # Return sanitized string
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

        class parser:
            class useragent:
                endpoint_url = 'parser/useragent'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_day=10000)
                cache_timeout = 5

                title = 'User-Agent Parser'
                description = 'Parse user-agent string to get OS, browser, and device information. If no "query" parameter is provided, the "User-Agent" header will be used.'
                parameters = {
                    'query': {'description': 'User-Agent string to be parsed.', 'required': False, 'type': 'string'}
                }

                @staticmethod
                def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                    timer = APITools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    api_request_id = db_client.start_request(request_data, timer.start_time)

                    # Request data validation
                    if request_data['args'].get('query'): ua_string = request_data['args']['query']
                    elif request_data['headers'].get('User-Agent'): ua_string = request_data['headers']['User-Agent']
                    else:
                        output_data['api']['errorMessage'] = 'No "query" parameter or "User-Agent" header found in the request.'
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

            class url:
                endpoint_url = 'parser/url'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_day=10000)
                cache_timeout = 5

                title = 'URL Parser'
                description = 'Parse URL to get protocol, hostname, path, parameters, and fragment information.'
                parameters = {
                    'query': {'description': 'URL to be parsed.', 'required': True, 'type': 'string'}
                }

                @staticmethod
                def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                    timer = APITools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    api_request_id = db_client.start_request(request_data, timer.start_time)

                    # Request data validation
                    if request_data['args'].get('query'): url = request_data['args']['query']
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

            class sec_to_hms:
                endpoint_url = 'parser/sec-to-hms'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_day=10000)
                cache_timeout = 5

                title = 'Seconds to HH:MM:SS Converter'
                description = 'Convert seconds to HH:MM:SS format.'
                parameters = {
                    'query': {'description': 'Seconds to be converted.', 'required': True, 'type': 'integer'}
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
                endpoint_url = 'parser/email'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_day=10000)
                cache_timeout = 5

                title = 'E-mail Address Parser'
                description = 'Parse e-mail address to get user and domain information.'
                parameters = {
                    'query': {'description': 'E-mail address to be parsed.', 'required': True, 'type': 'string'}
                }

                @staticmethod
                def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                    timer = APITools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    api_request_id = db_client.start_request(request_data, timer.start_time)

                    # Request data validation
                    if request_data['args'].get('query'): email = request_data['args']['query']
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

            class text_counter:
                endpoint_url = 'parser/text-counter'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_day=10000)
                cache_timeout = 5

                title = 'Advanced Text Counter'
                description = 'Count the number of characters, words, and many other elements in a text.'
                parameters = {
                    'query': {'description': 'Text to be analyzed.', 'required': True, 'type': 'string'}
                }

                @staticmethod
                def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                    timer = APITools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    api_request_id = db_client.start_request(request_data, timer.start_time)

                    # Request data validation
                    if request_data['args'].get('query'): text = request_data['args']['query']
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

        class tools:
            class text_lang_detector:
                endpoint_url = 'tools/text-lang-detector'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=4, per_day=800)
                cache_timeout = 3600

                title = 'Text Language Detector'
                description = 'Detects the predominant language in a text.'
                parameters = {
                    'query': {'description': 'Text to be analyzed.', 'required': True, 'type': 'string'}
                }

                @staticmethod
                def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                    timer = APITools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    api_request_id = db_client.start_request(request_data, timer.start_time)

                    # Request data validation
                    if request_data['args'].get('query'): text = request_data['args']['query']
                    else:
                        output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 400

                    # Main process
                    DetectorFactory.seed = 0

                    try: detected_lang = detect_lang(text)
                    except LangDetectException:
                        output_data['api']['errorMessage'] = "There aren't enough resources in the text to detect your language."
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 400

                    timer.stop()

                    output_data['response'] = {'detectedLangCode': detected_lang, 'detectedLangName': Language.get(detected_lang).display_name('en')}
                    output_data['api']['status'] = True
                    output_data['api']['elapsedTime'] = timer.elapsed_time()

                    db_client.update_request_status('success', api_request_id, timer.end_time)

                    return output_data, 200

            class text_translator:
                endpoint_url = 'tools/text-translator'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=4, per_day=600)
                cache_timeout = 3600

                title = 'Text Translator'
                description = 'Translate text from one language to another.'
                parameters = {
                    'query': {'description': 'Text to be translated.', 'required': True, 'type': 'string'},
                    'src_lang': {'description': 'Source language code (e.g., "pt" for Portuguese). If not provided, the language will be automatically detected.', 'required': False, 'type': 'string'},
                    'dest_lang': {'description': 'Destination language code (e.g., "en" for English).', 'required': True, 'type': 'string'}
                }

                @staticmethod
                def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                    timer = APITools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    api_request_id = db_client.start_request(request_data, timer.start_time)

                    # Request data validation
                    if request_data['args'].get('query'): text = request_data['args']['query']
                    else:
                        output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 400

                    if request_data['args'].get('dest_lang'): dest_lang = str(request_data['args']['dest_lang']).replace('-', '_')
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

            class ip:
                endpoint_url = 'tools/ip'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=10, per_day=10000)
                cache_timeout = 5

                title = 'IP Address Retriever'
                description = 'Get your IP address from the request.'
                parameters = {}

                @staticmethod
                def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                    timer = APITools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    api_request_id = db_client.start_request(request_data, timer.start_time)

                    # Request data validation
                    if request_data.get('ipAddress'): ip = request_data['ipAddress']
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

            class latest_ffmpeg_download_url:
                endpoint_url = 'tools/latest-ffmpeg-download-url'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=1, per_min=20, per_day=600)
                cache_timeout = 14400

                title = 'Latest FFmpeg Download URL Generator'
                description = 'Get the latest FFmpeg download url according to your specifications.'
                parameters = {
                    'os': {'description': 'Operating system (options: "windows", "linux").', 'required': False, 'type': 'string'},
                    'arch': {'description': 'Architecture (options: "amd32", "amd64", "arm32", "arm64").', 'required': False, 'type': 'string'},
                    'license': {'description': 'License type (options: "gpl", "lgpl").', 'required': False, 'type': 'string'},
                    'shared': {'description': 'Whether the FFmpeg build is shared or not (options: "true", "false").', 'required': False, 'type': 'boolean'}
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

                    matched_builds = list(set(builds))

                    if not matched_builds:
                        output_data['api']['errorMessage'] = 'No FFmpeg build found with the specified parameters.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 404

                    timer.stop()

                    output_data['response'] = {'matchedBuilds': matched_builds}
                    output_data['api']['status'] = True
                    output_data['api']['elapsedTime'] = timer.elapsed_time()

                    db_client.update_request_status('success', api_request_id, timer.end_time)

                    return output_data, 200

            class video_url_info:
                endpoint_url = 'tools/video-url-info'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=60, per_day=600)
                cache_timeout = 3600

                title = 'Video URL Information Extractor'
                description = 'Extracts information from a video URL.'
                parameters = {
                    'query': {'description': 'Video URL to be analyzed.', 'required': True, 'type': 'string'}
                }

                @staticmethod
                def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                    timer = APITools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    api_request_id = db_client.start_request(request_data, timer.start_time)

                    # Request data validation
                    if request_data['args'].get('query'): url = request_data['args']['query']
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
                        print(e)
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

        class scraper:
            class google_search:
                endpoint_url = 'scraper/google-search'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=30, per_day=400)
                cache_timeout = 3600

                title = 'Google Search'
                description = 'Searches and returns Google results according to your query.'
                parameters = {
                    'query': {'description': 'Search query.', 'required': True, 'type': 'string'},
                    'max_results': {'description': 'Maximum number of results to be returned (default: 10, max: 50).', 'required': False, 'type': 'integer'}
                }

                @staticmethod
                def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                    timer = APITools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    api_request_id = db_client.start_request(request_data, timer.start_time)

                    # Request data validation
                    if request_data['args'].get('query'): query = request_data['args']['query']
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
                    search_results = list()
                    for result in google_search(query, num_results=max_results, lang='en'):
                        search_results.append(unquote(result))

                    search_results = list(set(search_results))

                    timer.stop()

                    output_data['response'] = {'searchResults': search_results}
                    output_data['api']['status'] = True
                    output_data['api']['elapsedTime'] = timer.elapsed_time()

                    db_client.update_request_status('success', api_request_id, timer.end_time)

                    return output_data, 200

            class instagram_reels:
                endpoint_url = 'scraper/instagram-reels'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=30, per_day=400)
                cache_timeout = 28800

                title = 'Instagram Reels Scraper'
                description = 'Fetches permanent data from any Instagram reels URL.'
                parameters = {
                    'query': {'description': 'Instagram Reels URL.', 'required': True, 'type': 'string'}
                }

                @staticmethod
                def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                    timer = APITools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    api_request_id = db_client.start_request(request_data, timer.start_time)

                    # Request data validation
                    if request_data['args'].get('query'): query = request_data['args']['query']
                    else:
                        output_data['api']['errorMessage'] = 'No "query" parameter found in the request.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 400

                    def is_valid_instagram_reel_url(query: AnyStr) -> bool:
                        """
                        Check if the URL is a valid Instagram Reels URL.
                        :param query: URL to be checked.
                        :return: True if the URL is a valid Instagram Reels URL, False otherwise.
                        """

                        pattern = re_compile(r'^(https?://)?(www\.)?instagram\.com(/[^/]+)?/(reel|p)/[A-Za-z0-9_-]+/?(\?.*)?$')
                        return bool(pattern.match(query))

                    if not is_valid_instagram_reel_url(query):
                        output_data['api']['errorMessage'] = r'The URL provided is not a valid Instagram Reels URL. A valid URL should look like: https://www.instagram.com/reel/{your_reel_id}'
                        return output_data, 400

                    # Main process
                    def safe_unquote_url(url: AnyStr) -> str:
                        """
                        Safely unquote URL.
                        :param url: URL to be unquoted.
                        :return: Unquoted URL.
                        """

                        parsed_url = urlparse(url)
                        unquoted_url_base = unquote_plus(parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path)
                        unquoted_url = str(unquoted_url_base + '?' + urlencode(parse_qs(parsed_url.query), doseq=True))

                        return unquoted_url

                    def edit_url_param(url: AnyStr, param: AnyStr, new_value: AnyStr) -> str:
                        """
                        Edit a parameter in the URL.
                        :param url: URL to be edited.
                        :param param: Parameter to be edited.
                        :param new_value: New value for the parameter.
                        :return: Edited URL with the new parameter value.
                        """

                        parsed_url = urlparse(url)
                        query_dict = parse_qs(parsed_url.query)

                        if param in query_dict: query_dict[param] = new_value
                        else: query_dict[param] = [new_value]

                        edited_url = parsed_url._replace(query=urlencode(query_dict, doseq=True)).geturl()

                        return edited_url

                    if not urlparse(query).scheme: query = 'https://' + query

                    try:
                        response = post('https://fastdl.app/api/convert', headers={'User-Agent': fake_useragent.random, 'Accept': 'application/json'}, json={'url': query}, timeout=10)
                    except HTTPError:
                        output_data['api']['errorMessage'] = 'Some error occurred in our systems during the data search. Please try again later.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 500

                    if response.status_code != 200 or not response.json():
                        output_data['api']['errorMessage'] = 'Some external error occurred during the data search. Please try again later.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 500

                    response_data = response.json()

                    try:
                        filename = format_string(response_data['meta']['title']) + '.' + response_data.get('url', list(dict()))[0].get('ext', 'mp4').lower()
                        thumbnail_url = safe_unquote_url(edit_url_param(parse_qs(urlparse(response_data['thumb']).query)['uri'][0], 'dl', '0'))
                        media_url = safe_unquote_url(edit_url_param(parse_qs(urlparse(response_data['url'][0]['url']).query)['uri'][0], 'dl', '0'))
                    except BaseException:
                        output_data['api']['errorMessage'] = 'An error occurred while fetching Instagram reel data. Please try again later.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 500

                    timer.stop()

                    output_data['response'] = {'filename': filename, 'thumbnailUrl': thumbnail_url, 'mediaUrl': media_url}
                    output_data['api']['status'] = True
                    output_data['api']['elapsedTime'] = timer.elapsed_time()

                    db_client.update_request_status('success', api_request_id, timer.end_time)

                    return output_data, 200

            class tiktok_media:
                endpoint_url = 'scraper/tiktok-media'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=30, per_day=400)
                cache_timeout = 28800

                title = 'TikTok Media Scraper'
                description = 'Fetches permanent data from any TikTok video URL.'
                parameters = {
                    'query': {'description': 'TikTok video URL.', 'required': True, 'type': 'string'}
                }

                @staticmethod
                def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                    timer = APITools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    api_request_id = db_client.start_request(request_data, timer.start_time)

                    # Request data validation
                    if request_data['args'].get('query'): query = request_data['args']['query']
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
                        temp_response = get('https://www.tiktok.com/oembed', params={'url': query}, headers={'User-Agent': fake_useragent.random}, timeout=10)
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
                        response = post('https://savetik.co/api/ajaxSearch', headers={'User-Agent': fake_useragent.random, 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}, data={'q': query}, timeout=10)
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

            class youtube_media:
                endpoint_url = 'scraper/youtube-media'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=1, per_min=20, per_day=300)
                cache_timeout = 14400

                title = 'YouTube Media Scraper'
                description = 'Get detailed data from any YouTube video URL.'
                parameters = {
                    'query': {'description': 'YouTube video URL.', 'required': True, 'type': 'string'}
                }

                @staticmethod
                def run(db_client: psycopg2_connect, request_data: Dict[str, Dict[Any, Any]]) -> Tuple[dict, int]:
                    timer = APITools.Timer()
                    output_data = APITools.get_default_api_output_dict()

                    api_request_id = db_client.start_request(request_data, timer.start_time)

                    # Request data validation
                    if request_data['args'].get('query'): query = request_data['args']['query']
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
                        output_data['api']['errorMessage'] = 'The URL provided is not a valid YouTube media URL.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 400
                    elif parsed_url_data['urlType'] != 'video':
                        output_data['api']['errorMessage'] = 'Only video URLs are supported for now.'
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 400

                    # Main process
                    def extract_media_info(data: dict) -> dict:
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

                    def extract_media_subtitles(data: dict) -> list:
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
                        adjusted_yt_data = {'info': extract_media_info(raw_yt_extracted_data), 'media': {'video': list(), 'audio': list(), 'subtitles': list()}}
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
                    yt_media_data['subtitles'] = extract_media_subtitles(raw_yt_extracted_data)

                    timer.stop()

                    output_data['response'] = adjusted_yt_data
                    output_data['api']['status'] = True
                    output_data['api']['elapsedTime'] = timer.elapsed_time()

                    db_client.update_request_status('success', api_request_id, timer.end_time)

                    return output_data, 200

            class youtube_video_url_from_query:
                endpoint_url = 'scraper/youtube-video-url-from-query'
                allowed_methods = ['GET']
                ratelimit = LimiterTools.gen_ratelimit_message(per_sec=2, per_min=60, per_day=1000)
                cache_timeout = 3600

                title = 'YouTube Video URL Generator'
                description = 'Generates a YouTube video URL from a search query.'
                parameters = {
                    'query': {'description': 'Search query.', 'required': True, 'type': 'string'}
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
                    try:
                        scraped_data = SearchYouTubeVideos(query, offset=1, mode='dict', max_results=1).result()['search_result'][0]
                    except Exception as e:
                        output_data['api']['errorMessage'] = str(e)
                        db_client.log_exception(api_request_id, output_data['api']['errorMessage'], timer.get_time())
                        return output_data, 500

                    channel_id = str(scraped_data.get('channeId'))
                    channel_url = f'https://www.youtube.com/channel/{channel_id}'
                    channel_name = str(scraped_data.get('channel'))
                    formated_channel_name = format_string(channel_name)
                    media_title = str(scraped_data.get('title'))
                    formatted_media_title = format_string(media_title)
                    media_id = str(scraped_data.get('id'))
                    view_count = int(scraped_data.get('views'))
                    media_url = f'https://www.youtube.com/watch?v={media_id}'
                    media_short_url = f'https://youtu.be/{media_id}'
                    media_embed_url = f'https://www.youtube.com/embed/{media_id}'
                    thumbnail_urls = [
                        f'https://img.youtube.com/vi/{media_id}/maxresdefault.jpg',
                        f'https://img.youtube.com/vi/{media_id}/sddefault.jpg',
                        f'https://img.youtube.com/vi/{media_id}/hqdefault.jpg',
                        f'https://img.youtube.com/vi/{media_id}/mqdefault.jpg',
                        f'https://img.youtube.com/vi/{media_id}/default.jpg'
                    ]

                    adjusted_yt_data = {
                        'mediaId': media_id,
                        'mediaTitle': media_title,
                        'formattedMediaTitle': formatted_media_title,
                        'viewCount': view_count,
                        'mediaUrl': media_url,
                        'mediaShortUrl': media_short_url,
                        'mediaEmbedUrl': media_embed_url,
                        'channelId': channel_id,
                        'channelUrl': channel_url,
                        'channelName': channel_name,
                        'formattedChannelName': formated_channel_name,
                        'thumbnailUrls': thumbnail_urls
                    }

                    timer.stop()

                    output_data['response'] = {'foundUrlData': adjusted_yt_data}
                    output_data['api']['status'] = True
                    output_data['api']['elapsedTime'] = timer.elapsed_time()

                    db_client.update_request_status('success', api_request_id, timer.end_time)

                    return output_data, 200
