from flask import Flask, request, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from re import compile as re_compile
from dotenv import load_dotenv
from os import getenv
from typing import Any, Union

from api_resources.main_endpoints.ai.v1.ask_gemini import main as ai__ask_gemini

from api_resources.main_endpoints.randomizer.v1.int_number import main as randomizer__int_number
from api_resources.main_endpoints.randomizer.v1.float_number import main as randomizer__float_number

from api_resources.main_endpoints.scraper.v1.file_mediafire0com import main as scraper__file_mediafire0com
from api_resources.main_endpoints.scraper.v1.file_drive0google0com import main as scraper__file_drive0google0com
from api_resources.main_endpoints.scraper.v1.file_pillowcase0su import main as scraper__file_pillowcase0su
from api_resources.main_endpoints.scraper.v1.product_aliexpress0com import main as scraper__product_aliexpress0com
from api_resources.main_endpoints.scraper.v1.video_youtube0com import main as scraper__video_youtube0com
from api_resources.main_endpoints.scraper.v1.product_promotions import main as scraper__product_promotions

from api_resources.main_endpoints.others.v1.whoami import main as others__whoami
from api_resources.main_endpoints.others.v1.ua_info import main as others__ua_info
from api_resources.main_endpoints.others.v1.ip_info import main as others__ip_info


# Load environment variables from .env files
load_dotenv()

# Get environment variables values
flask_port = int(getenv('FLASK_PORT'))
# redis_server_url = str(env_settings.get('REDIS_SERVER_URL'))  # Uncomment this line if you want to use Redis as a cache server

gemini_api_keys = list()
gemini_api_keys.append(getenv('GEMINI_API_KEY_1'))
gemini_api_keys.append(getenv('GEMINI_API_KEY_2'))

# Initialize Flask app and your plugins
app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'  # Change to "redis" if you want to use Redis as a cache server
# app.config['CACHE_REDIS_URL'] = redis_server_url  # Uncomment this line if you want to use Redis as a cache server
limiter = Limiter(app=app, key_func=get_remote_address, storage_uri='memory://')
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
    'base_api_url': 'https://everytoolsapi.onrender.com',
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
            'video-youtube.com': {
                'description': 'Extracts accurate information from an existing video on "youtube.com" and returns it in an easy-to-understand JSON format.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/scraper/v1/video-youtube.com',
                'full_endpoint_url': '/api/scraper/v1/video-youtube.com?id=',
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
        },
        'others': {
            'whoami': {
                'description': 'Get information about your request, such as IPv4, IPv6 (if available) and User-Agent.',
                'rate_limit': get_rate_limit_message(2, 60, 3600, 30000),
                'cache_timeout': 1,
                'allowed_methods': ['GET'],
                'base_endpoint_url': '/api/others/v1/whoami',
                'full_endpoint_url': '/api/others/v1/whoami',
                'parameters': {
                    'required': [],
                    'optional': []
                },
            },
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
                    'required': [],
                    'optional': [
                        {'name': 'ip', 'type': 'string', 'description': 'The IPv4 or IPv6 address you want to get the information.'}
                    ]
                },
            },
        },
    }
}

# Flask error handlers
@app.errorhandler(404)
@cache.cached(timeout=28800, make_cache_key=_make_cache_key)
def weberror_404(_) -> tuple[dict, int]:
    return {'success': False, 'message': 'The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.'}, 404


@app.errorhandler(429)
@cache.cached(timeout=28800, make_cache_key=_make_cache_key)
def weberror_429(_) -> tuple[dict, int]:
    return ({'success': False, 'message': 'You have exceeded the rate limit! Please wait a few seconds and try again.'}), 429


# Flask general routes
@app.route('/', methods=['GET'])
def homepage() -> redirect:
    return redirect('/docs', code=302)


@app.route('/api', methods=['GET'])
@cache.cached(timeout=28800, make_cache_key=_make_cache_key)
def api() -> tuple[dict, int]:
    return {'success': True, 'message': 'The API is online and working.'}, 200


@app.route('/status', methods=['GET'])
@cache.cached(timeout=86400, make_cache_key=_make_cache_key)
def status() -> redirect:
    return redirect('https://1r23r6r9.status.cron-job.org', code=302)


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


# Route: /api/scraper/v?/video-youtube.com
_data_scraper__video_youtube0com = endpoints_data['endpoints']['scraper']['video-youtube.com']
@app.route(_data_scraper__video_youtube0com['base_endpoint_url'].split('?')[0], methods=['GET'])
@limiter.limit(_data_scraper__video_youtube0com['rate_limit'])
@cache.cached(timeout=_data_scraper__video_youtube0com['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__video_youtube0com() -> tuple[dict, int]:
    p_id = request.args.get('id')

    if not p_id or not re_compile(r'^[a-zA-Z0-9_-]+$').match(p_id):
        return get_output_response_data(False, 'The id parameter is required and must be alphanumeric.'), 400

    output_data = scraper__video_youtube0com(p_id)

    if output_data:
        return get_output_response_data(True, output_data['data'], _data_scraper__video_youtube0com['description'], output_data['processing_time']), 200
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


# Route: /api/others/v?/whoami
_data_others__whoami = endpoints_data['endpoints']['others']['whoami']
@app.route(_data_others__whoami['base_endpoint_url'], methods=['GET'])
@limiter.limit(_data_others__whoami['rate_limit'])
@cache.cached(timeout=_data_others__whoami['cache_timeout'], make_cache_key=_make_cache_key)
def _others__whoami() -> tuple[dict, int]:
    return _route_in_maintenance()

    output_data = others__whoami(request.headers.__dict__)

    if output_data:
        return get_output_response_data(True, output_data['data'], _data_others__whoami['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, 'An error occurred while trying to get the IP address. Please try again later.'), 404


# Route: /api/others/v?/ua-info
_data_others__ua_info = endpoints_data['endpoints']['others']['ua-info']
@app.route(_data_others__ua_info['base_endpoint_url'], methods=['GET'])
@limiter.limit(_data_others__ua_info['rate_limit'])
@cache.cached(timeout=_data_others__ua_info['cache_timeout'], make_cache_key=_make_cache_key)
def _others__ua_info() -> tuple[dict, int]:
    p_ua = request.args.get('ua')

    output_data = others__ua_info(request.headers.__dict__, p_ua)

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
    return _route_in_maintenance()
    
    p_ip = request.args.get('ip')

    output_data = others__ip_info(request.headers.__dict__, p_ip)

    if output_data:
        return get_output_response_data(True, output_data['data'], _data_others__ip_info['description'], output_data['processing_time']), 200
    else:
        return get_output_response_data(False, 'An error occurred while trying to search for the IP address. Please try again later or check if the IP address is valid.'), 404


if __name__ == '__main__':
    app.config['JSON_SORT_KEYS'] = True
    app.run(host='0.0.0.0', port=flask_port, threaded=True, debug=False)
