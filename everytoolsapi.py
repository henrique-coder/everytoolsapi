from flask import Flask, request, redirect, render_template
from flask_limiter import util as flask_limiter_utils, Limiter
from flask_caching import Cache
from re import compile as re_compile, match as re_match
from dotenv import load_dotenv
from os import getenv
from pathlib import Path
from typing import Any, Union

from api_resources.main_endpoints.ai.v1.ask_gemini import main as ai__ask_gemini

from api_resources.main_endpoints.randomizer.v1.int_number import main as randomizer__int_number
from api_resources.main_endpoints.randomizer.v1.float_number import main as randomizer__float_number

from api_resources.main_endpoints.scraper.v1.file_mediafire0com import main as scraper__file_mediafire0com
from api_resources.main_endpoints.scraper.v1.file_drive0google0com import main as scraper__file_drive0google0com
from api_resources.main_endpoints.scraper.v1.file_pillowcase0su import main as scraper__file_pillowcase0su
from api_resources.main_endpoints.scraper.v1.product_aliexpress0com import main as scraper__product_aliexpress0com
from api_resources.main_endpoints.scraper.v1.media_youtube0com import main as scraper__media_youtube0com
from api_resources.main_endpoints.scraper.v1.product_promotions import main as scraper__product_promotions
from api_resources.main_endpoints.scraper.v1.music_soundcloud0com import main as scraper__music_soundcloud0com

from api_resources.main_endpoints.others.v1.ua_info import main as others__ua_info
from api_resources.main_endpoints.others.v1.ip_info import main as others__ip_info


# Load environment variables from .env files
load_dotenv()

# Get environment variables values
flask_port = int(getenv('FLASK_PORT'))
# redis_server_url = str(getenv('REDIS_SERVER_URL'))  # Uncomment this line if you want to use Redis as a cache server

gemini_api_keys = list()
gemini_api_keys.append(getenv('GEMINI_API_KEY_1'))
gemini_api_keys.append(getenv('GEMINI_API_KEY_2'))

# Initialize Flask app and your plugins
app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'  # Change to "redis" if you want to use Redis as a cache server
# app.config['CACHE_REDIS_URL'] = redis_server_url  # Uncomment this line if you want to use Redis as a cache server
limiter = Limiter(app=app, key_func=flask_limiter_utils.get_remote_address, storage_uri='memory://')  # Change storage_uri to "redis" if you want to use Redis as a cache server
cache = Cache(app)


# General functions
def get_rate_limit_message(requests_per_second: int, requests_per_minute: int, requests_per_hour: int, requests_per_day: int) -> str:
    return f'{requests_per_second}/second;{requests_per_minute}/minute;{requests_per_hour}/hour;{requests_per_day}/day'


def get_output_response_data(success: bool, data: Union[dict, str], endpoint_description: str = None, processing_time: float = None) -> dict:
    if success:
        return {
            'response': data,
            'api': {
                'success': True,
                'processing_time': processing_time,
                'description': endpoint_description
            }
        }
    else:
        return {
            'api': {
                'success': False,
                'message': data
            }
        }


# Flask required functions
def _make_cache_key(*args, **kwargs) -> str:
    return request.url


def _route_in_maintenance() -> tuple[dict, int]:
    return {'success': False, 'message': 'This endpoint is under maintenance. Please try again later.'}, 503


# Endpoints data
endpoints_data = {
    'message': 'Welcome to the EveryTools API. Where you can find all the tools you need in one place.',
    'source_code_url': 'https://github.com/Henrique-Coder/everytoolsapi',
    'base_api_url': 'https://everytoolsapi-henrique-coder.koyeb.app',
    'endpoints': {
        'ai': {
            'ask-gemini': {
                'description': 'Ask a question to Gemini AI and get an answer. You can also provide an image to help the AI understand the context better.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 5,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/ai/v1/ask-gemini',
                'full_endpoint_url': '/api/ai/v1/ask-gemini?prompt=&image_url=',
                'parameters': {
                    'required': [
                        {'name': 'prompt', 'type': 'string', 'description': 'The question you want to ask to the AI.'},
                    ],
                    'optional': [
                        {'name': 'image_url', 'type': 'string', 'description': 'An image URL to help the AI understand the context better.'},
                    ]
                },
            },
        },
        'randomizer': {
            'int-number': {
                'description': 'Generate a random integer number between the specified minimum and maximum values.',
                'rate_limit': get_rate_limit_message(5, 300, 18000, 30000),
                'cache_timeout': 1,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/randomizer/v1/int-number',
                'full_endpoint_url': '/api/randomizer/v1/int-number?min=&max=',
                'parameters': {
                    'required': [
                        {'name': 'min', 'type': 'integer', 'description': 'The minimum value for the random number.'},
                        {'name': 'max', 'type': 'integer', 'description': 'The maximum value for the random number.'},
                    ],
                    'optional': []
                },
            },
            'float-number': {
                'description': 'Generate a random float number between the specified minimum and maximum values.',
                'rate_limit': get_rate_limit_message(5, 300, 18000, 30000),
                'cache_timeout': 1,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/randomizer/v1/float-number',
                'full_endpoint_url': '/api/randomizer/v1/float-number?min=&max=',
                'parameters': {
                    'required': [
                        {'name': 'min', 'type': 'float', 'description': 'The minimum value for the random number.'},
                        {'name': 'max', 'type': 'float', 'description': 'The maximum value for the random number.'},
                    ],
                    'optional': []
                },
            }
        },
        'scraper': {
            'file-mediafire.com': {
                'description': 'Generates a direct and permanent link to a file hosted in "mediafire.com" and returns it.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/scraper/v1/file-mediafire.com',
                'full_endpoint_url': '/api/scraper/v1/file-mediafire.com?id=',
                'parameters': {
                    'required': [
                        {'name': 'id', 'type': 'alphanumeric', 'description': 'The file ID you want to get the direct link.'},
                    ],
                    'optional': []
                },
            },
            'file-drive.google.com': {
                'description': 'Generates a direct and temporary link to a file hosted in "drive.google.com" and returns it.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/scraper/v1/file-drive.google.com',
                'full_endpoint_url': '/api/scraper/v1/file-drive.google.com?id=',
                'parameters': {
                    'required': [
                        {'name': 'id', 'type': 'alphanumeric', 'description': 'The file ID you want to get the direct link.'},
                    ],
                    'optional': []
                },
            },
            'file-pillowcase.su': {
                'description': 'Generates a direct and permanent link to a file hosted in "pillowcase.su" and returns it.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/scraper/v1/file-pillowcase.su',
                'full_endpoint_url': '/api/scraper/v1/file-pillowcase.su?id=',
                'parameters': {
                    'required': [
                        {'name': 'id', 'type': 'alphanumeric', 'description': 'The file ID you want to get the direct link.'},
                    ],
                    'optional': []
                },
            },
            'product-aliexpress.com': {
                'description': 'Extracts accurate information from an existing product on "aliexpress.com" and returns it in an easy-to-understand JSON format.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/scraper/v1/product-aliexpress.com',
                'full_endpoint_url': '/api/scraper/v1/product-aliexpress.com?id=',
                'parameters': {
                    'required': [
                        {'name': 'id', 'type': 'numeric', 'description': 'The product ID you want to get the information.'},
                    ],
                    'optional': []
                },
            },
            'media-youtube.com': {
                'description': 'Extracts accurate information from an existing video on "youtube.com" and returns it in an easy-to-understand JSON format.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/scraper/v1/media-youtube.com',
                'full_endpoint_url': '/api/scraper/v1/media-youtube.com?id=',
                'parameters': {
                    'required': [
                        {'name': 'id', 'type': 'alphanumeric', 'description': 'The video ID you want to get the information.'},
                    ],
                    'optional': []
                },
            },
            'product-promotions': {
                'description': 'Search for active promotions of a product in multiple stores and return them in an easy-to-understand JSON format.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/scraper/v1/product-promotions',
                'full_endpoint_url': '/api/scraper/v1/product-promotions?name=',
                'parameters': {
                    'required': [
                        {'name': 'name', 'type': 'string', 'description': 'The product name you want to get the promotions.'},
                    ],
                    'optional': []
                },
            },
            'music-soundcloud.com': {
                'description': 'Extracts accurate information from an existing music on "soundcloud.com" and returns it in an easy-to-understand JSON format.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/scraper/v1/music-soundcloud.com',
                'full_endpoint_url': '/api/scraper/v1/music-soundcloud.com?url=',
                'parameters': {
                    'required': [
                        {'name': 'url', 'type': 'string', 'description': 'The music URL you want to get the information.'},
                    ],
                    'optional': []
                },
            }
        },
        'others': {
            'ua-info': {
                'description': 'Parse a input User-Agent string or the User-Agent string of the request and return it in an easy-to-understand JSON format.',
                'rate_limit': get_rate_limit_message(1, 60, 3600, 30000),
                'cache_timeout': 3600,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/others/v1/ua-info',
                'full_endpoint_url': '/api/others/v1/ua-info?ua=',
                'parameters': {
                    'required': [],
                    'optional': [
                        {'name': 'ua', 'type': 'string', 'description': 'The User-Agent string you want to parse.'}
                    ],
                },
            },
            'ip-info': {
                'description': 'Get information about an IPv4 or IPv6 address and return it in an easy-to-understand JSON format.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 3600,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/others/v1/ip-info',
                'full_endpoint_url': '/api/others/v1/ip-info?ip=',
                'parameters': {
                    'required': [
                        {'name': 'ip', 'type': 'string', 'description': 'The IPv4 or IPv6 address you want to get the information.'}
                    ],
                    'optional': []
                },
            },
        },
    }
}


# Flask error handlers
def show_error_page(error_code: int, error_name: str = None):
    if not error_name:
        if error_code == 404:
            error_name = 'Not Found'
        elif error_code == 429:
            error_name = 'Rate Limit Exceeded'
        elif error_code == 500:
            error_name = 'Internal Server Error'
        else:
            error_name = 'Unknown Error'

    return render_template('global_error_page.html', error_code=error_code, error_name=error_name), error_code


@app.errorhandler(404)
@cache.cached(timeout=28800, make_cache_key=_make_cache_key)
def weberror_404(_) -> render_template:
    return show_error_page(404)


@app.errorhandler(429)
@cache.cached(timeout=28800, make_cache_key=_make_cache_key)
def weberror_429(_) -> render_template:
    return show_error_page(429)


@app.errorhandler(500)
@cache.cached(timeout=28800, make_cache_key=_make_cache_key)
def weberror_500(_) -> render_template:
    return show_error_page(500)


# Flask general routes
@app.route('/api', methods=['GET', 'HEAD'])
@cache.cached(timeout=28800, make_cache_key=_make_cache_key)
def api() -> tuple[dict, int]:
    return {'success': True, 'message': 'The API is online and working.'}, 200


@app.route('/', methods=['GET'])
def initial_page() -> redirect:
    return redirect('/docs', code=301)


@app.route('/docs', methods=['GET'])
@cache.cached(timeout=28800, make_cache_key=_make_cache_key)
def docs() -> tuple[dict, int]:
    return endpoints_data, 200


# Flask API routes

# Route: /api/ai/v?/ask-gemini
_data_route_ai__ask_gemini = endpoints_data['endpoints']['ai']['ask-gemini']
@app.route(_data_route_ai__ask_gemini['base_endpoint_url'], methods=_data_route_ai__ask_gemini['allowed_methods'])
@limiter.limit(_data_route_ai__ask_gemini['rate_limit'])
@cache.cached(timeout=_data_route_ai__ask_gemini['cache_timeout'], make_cache_key=_make_cache_key)
def _ai__ask_gemini() -> tuple[dict, int]:
    p_prompt = request.args.get('prompt')
    p_image_url = request.args.get('image_url')

    if not p_prompt or not str(p_prompt).strip():
        return get_output_response_data(False, 'The prompt parameter is required.'), 400

    output_data = ai__ask_gemini(gemini_api_keys, p_prompt, p_image_url)

    if output_data:
        return get_output_response_data(True, output_data['data'], _data_route_ai__ask_gemini['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, f'An error occurred while trying to generate the response. Tip: make sure the image URL is valid and has one of the following MIME types: image/png, image/jpeg, image/webp, image/heic or image/heif.'), 404


# Route: /api/randomizer/v?/int-number
_data_route_randomizer__int_number = endpoints_data['endpoints']['randomizer']['int-number']
@app.route(_data_route_randomizer__int_number['base_endpoint_url'], methods=['GET'])
@limiter.limit(_data_route_randomizer__int_number['rate_limit'])
@cache.cached(timeout=_data_route_randomizer__int_number['cache_timeout'], make_cache_key=_make_cache_key)
def _randomizer__int_number() -> tuple[dict, int]:
    p_min = request.args.get('min')
    p_max = request.args.get('max')

    if not p_min or not p_min.isnumeric() or not p_max or not p_max.isnumeric():
        return get_output_response_data(False, 'The min and max parameters are required and must be integers.'), 400

    p_min, p_max = int(p_min), int(p_max)
    if p_min > p_max:
        return get_output_response_data(False, 'The min parameter must be less than the max parameter.'), 400

    output_data = randomizer__int_number(p_min, p_max)

    if output_data:
        return get_output_response_data(True, {'number': output_data['data']}, _data_route_randomizer__int_number['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, 'An error occurred while generating the random number. Please check your query and try again.'), 404


# Route: /api/randomizer/v?/float-number
_data_route_randomizer__float_number = endpoints_data['endpoints']['randomizer']['float-number']
@app.route(_data_route_randomizer__float_number['base_endpoint_url'].split('?')[0], methods=['GET'])
@limiter.limit(_data_route_randomizer__float_number['rate_limit'])
@cache.cached(timeout=_data_route_randomizer__float_number['cache_timeout'], make_cache_key=_make_cache_key)
def _randomizer__float_number() -> tuple[dict, int]:
    def is_float(value: Any) -> bool:
        try:
            float(value)
            return True
        except Exception:
            return False

    p_min = request.args.get('min')
    p_max = request.args.get('max')

    if not p_min or not is_float(p_min) or not p_max or not is_float(p_max):
        return get_output_response_data(False, 'The min and max parameters are required and must be floats.'), 400

    p_min, p_max = float(p_min), float(p_max)
    if p_min > p_max:
        return get_output_response_data(False, 'The min parameter must be less than the max parameter.'), 400

    output_data = randomizer__float_number(float(p_min), float(p_max))

    if output_data:
        return get_output_response_data(True, {'number': output_data['data']}, _data_route_randomizer__float_number['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, 'An error occurred while generating the random number. Please check your query and try again.'), 404


# Route: /api/scraper/v?/file-mediafire.com
_data_route_scraper__file_mediafire0com = endpoints_data['endpoints']['scraper']['file-mediafire.com']
@app.route(_data_route_scraper__file_mediafire0com['base_endpoint_url'].split('?')[0], methods=['GET'])
@limiter.limit(_data_route_scraper__file_mediafire0com['rate_limit'])
@cache.cached(timeout=_data_route_scraper__file_mediafire0com['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__file_mediafire_com() -> tuple[dict, int]:
    p_id = request.args.get('id')

    if not p_id or not p_id.isalnum():
        return get_output_response_data(False, 'The id parameter is required and must be alphanumeric.'), 400

    output_data = scraper__file_mediafire0com(p_id)

    if output_data:
        return get_output_response_data(True, {'url': output_data['data']}, _data_route_scraper__file_mediafire0com['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, 'Query not found or invalid. Please check your query and try again.'), 404


# Route: /api/scraper/v?/file-drive.google.com
_data_route_scraper__file_drive0google0com = endpoints_data['endpoints']['scraper']['file-drive.google.com']
@app.route(_data_route_scraper__file_drive0google0com['base_endpoint_url'].split('?')[0], methods=['GET'])
@limiter.limit(_data_route_scraper__file_drive0google0com['rate_limit'])
@cache.cached(timeout=_data_route_scraper__file_drive0google0com['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__file_drive0google0com() -> tuple[dict, int]:
    p_id = request.args.get('id')

    if not p_id or not re_compile(r'^[a-zA-Z0-9_-]+$').match(p_id):
        return get_output_response_data(False, 'The id parameter is required and must be alphanumeric.'), 400

    output_data = scraper__file_drive0google0com(p_id)

    if output_data:
        return get_output_response_data(True, {'url': output_data['data']}, _data_route_scraper__file_drive0google0com['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, 'Query not found or invalid. Please check your query and try again.'), 404


# Route: /api/scraper/v?/file-pillowcase.su
_data_route_scraper__file_pillowcase0su = endpoints_data['endpoints']['scraper']['file-pillowcase.su']
@app.route(_data_route_scraper__file_pillowcase0su['base_endpoint_url'].split('?')[0], methods=['GET'])
@limiter.limit(_data_route_scraper__file_pillowcase0su['rate_limit'])
@cache.cached(timeout=_data_route_scraper__file_pillowcase0su['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__file_pillowcase0su() -> tuple[dict, int]:
    p_id = request.args.get('id')

    if not p_id or not p_id.isalnum():
        return get_output_response_data(False, 'The id parameter is required and must be alphanumeric.'), 400

    output_data = scraper__file_pillowcase0su(p_id)

    if output_data:
        return get_output_response_data(True, {'url': output_data['data']}, _data_route_scraper__file_pillowcase0su['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, 'Query not found or invalid. Please check your query and try again.'), 404


# Route: /api/scraper/v?/product-aliexpress.com
_data_scraper__product_aliexpress0com = endpoints_data['endpoints']['scraper']['product-aliexpress.com']
@app.route(_data_scraper__product_aliexpress0com['base_endpoint_url'].split('?')[0], methods=['GET'])
@limiter.limit(_data_scraper__product_aliexpress0com['rate_limit'])
@cache.cached(timeout=_data_scraper__product_aliexpress0com['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__product_aliexpress0com() -> tuple[dict, int]:
    p_id = request.args.get('id')

    if not p_id or not p_id.isnumeric():
        return get_output_response_data(False, 'The id parameter is required and must be numeric.'), 400

    output_data = scraper__product_aliexpress0com(str(p_id))

    if output_data:
        return get_output_response_data(True, output_data['data'], _data_scraper__product_aliexpress0com['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, 'Query not found or invalid. Please check your query and try again.'), 404


# Route: /api/scraper/v?/media-youtube.com
_data_scraper__media_youtube0com = endpoints_data['endpoints']['scraper']['media-youtube.com']
@app.route(_data_scraper__media_youtube0com['base_endpoint_url'].split('?')[0], methods=['GET'])
@limiter.limit(_data_scraper__media_youtube0com['rate_limit'])
@cache.cached(timeout=_data_scraper__media_youtube0com['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__media_youtube0com() -> tuple[dict, int]:
    p_id = request.args.get('id')

    if not p_id or not re_compile(r'^[a-zA-Z0-9_-]+$').match(p_id):
        return get_output_response_data(False, 'The id parameter is required and must be alphanumeric.'), 400

    output_data = scraper__media_youtube0com(p_id)

    if output_data:
        return get_output_response_data(True, output_data['data'], _data_scraper__media_youtube0com['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, 'Query not found or invalid. Please check your query and try again.'), 404


# Route: /api/scraper/v?/product-promotions
_data_scraper__product_promotions = endpoints_data['endpoints']['scraper']['product-promotions']
@app.route(_data_scraper__product_promotions['base_endpoint_url'].split('?')[0], methods=['GET'])
@limiter.limit(_data_scraper__product_promotions['rate_limit'])
@cache.cached(timeout=_data_scraper__product_promotions['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__product_promotions() -> tuple[dict, int]:
    p_name = request.args.get('name')

    if not p_name:
        return get_output_response_data(False, 'The name parameter is required.'), 400

    output_data = scraper__product_promotions(p_name)

    if output_data:
        return get_output_response_data(True, output_data['data'], _data_scraper__product_promotions['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, 'No active promotions were found for the chosen product. Please choose another product or change its name.'), 404


# Route: /api/scraper/v?/music-soundcloud.com
_data_scraper__music_soundcloud0com = endpoints_data['endpoints']['scraper']['music-soundcloud.com']
@app.route(_data_scraper__music_soundcloud0com['base_endpoint_url'].split('?')[0], methods=['GET'])
@limiter.limit(_data_scraper__music_soundcloud0com['rate_limit'])
@cache.cached(timeout=_data_scraper__music_soundcloud0com['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__music_soundcloud0com() -> tuple[dict, int]:
    def is_valid_soundcloud_track_url(url: str) -> bool:
        pattern = r'https://soundcloud.com/[\w-]+/[\w-]+$'
        return bool(re_match(pattern, url))

    p_url = request.args.get('url')

    if not p_url or not is_valid_soundcloud_track_url(p_url):
        return get_output_response_data(False, 'The url parameter is required.'), 400

    output_data = scraper__music_soundcloud0com(p_url)

    if output_data:
        return get_output_response_data(True, output_data['data'], _data_scraper__music_soundcloud0com['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, 'An error occurred while trying to get the music information. Please check the URL and try again.'), 404


# Route: /api/others/v?/ua-info
_data_others__ua_info = endpoints_data['endpoints']['others']['ua-info']
@app.route(_data_others__ua_info['base_endpoint_url'], methods=['GET'])
@limiter.limit(_data_others__ua_info['rate_limit'])
@cache.cached(timeout=_data_others__ua_info['cache_timeout'], make_cache_key=_make_cache_key)
def _others__ua_info() -> tuple[dict, int]:
    p_ua = request.args.get('ua')

    output_data = others__ua_info(request.user_agent, p_ua)

    if output_data:
        return get_output_response_data(True, output_data['data'], _data_others__ua_info['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, 'An error occurred while trying to parse the User-Agent. Please try again later.'), 404


# Route: /api/others/v?/ip-info
_data_others__ip_info = endpoints_data['endpoints']['others']['ip-info']
@app.route(_data_others__ip_info['base_endpoint_url'], methods=['GET'])
@limiter.limit(_data_others__ip_info['rate_limit'])
@cache.cached(timeout=_data_others__ip_info['cache_timeout'], make_cache_key=_make_cache_key)
def _others__ip_info() -> tuple[dict, int]:
    p_ip = request.args.get('ip')

    if not p_ip or not str(p_ip).strip():
        return get_output_response_data(False, 'The ip parameter is required.'), 400

    output_data = others__ip_info(p_ip)

    if output_data:
        return get_output_response_data(True, output_data['data'], _data_others__ip_info['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, 'An error occurred while trying to search for the IP address. Please try again later or check if the IP address is valid.'), 404


if __name__ == '__main__':
    app.static_folder = Path('./static').resolve()
    app.template_folder = Path('./static/templates').resolve()
    app.config['JSON_SORT_KEYS'] = True
    app.run(host='0.0.0.0', port=flask_port, threaded=True, debug=False)
