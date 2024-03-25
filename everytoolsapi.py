from flask import Flask, request, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from dotenv import dotenv_values
from re import compile as re_compile
from typing import Any


from api_resources.main_endpoints.ai.v1.ask_gemini import main as ai__ask_gemini

from api_resources.main_endpoints.randomizer.v1.int_number import main as randomizer__int_number
from api_resources.main_endpoints.randomizer.v1.float_number import main as randomizer__float_number

from api_resources.main_endpoints.scraper.v1.file_mediafire0com import main as scraper__file_mediafire0com
from api_resources.main_endpoints.scraper.v1.file_drive0google0com import main as scraper__file_drive0google0com
from api_resources.main_endpoints.scraper.v1.file_gofile0io import main as scraper__file_gofile0io
from api_resources.main_endpoints.scraper.v1.file_pillowcase0su import main as scraper__file_pillowcase0su
from api_resources.main_endpoints.scraper.v1.product_aliexpress0com import main as scraper__product_aliexpress0com
from api_resources.main_endpoints.scraper.v1.video_youtube0com import main as scraper__video_youtube0com
from api_resources.main_endpoints.scraper.v1.product_promotions import main as scraper__product_promotions


# Load environment variables
env_vars = dotenv_values('.env')

# Load Gemini API keys
gemini_api_keys = list()

for key, value in env_vars.items():
    if key.startswith('GEMINI_API_KEY_'):
        gemini_api_keys.append(value)

# Initialize Flask app and your plugins
app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'
limiter = Limiter(app=app, key_func=get_remote_address, storage_uri='memory://')
cache = Cache(app)


# General functions
def get_rate_limit_message(requests_per_second: int, requests_per_minute: int, requests_per_hour: int, requests_per_day: int) -> str:
    return f'{requests_per_second}/second;{requests_per_minute}/minute;{requests_per_hour}/hour;{requests_per_day}/day'


def get_success_response_message(processing_time: float, response_data: dict, endpoint_description: str) -> dict:
    return {
        'api': {
            'success': True,
            'processing_time': processing_time,
            'description': endpoint_description
        },
        'response': response_data,
    }


def get_error_response_message(error_message: str) -> dict:
    return {
        'api': {
            'success': False,
            'message': error_message
        }
    }


# Flask required functions
def _make_cache_key(*args, **kwargs) -> str:
    return f'{request.url}{str(request.args)}'


def _route_in_maintenance() -> tuple[dict, int]:
    return {'success': False, 'message': 'This endpoint is under maintenance. Please try again later.'}, 503


# Endpoints data
endpoints_data = {
    'message': 'Welcome to the EveryTools API. Where you can find all the tools you need in one place.',
    'source_code_url': 'https://github.com/Henrique-Coder/everytoolsapi',
    'base_api_url': 'https://everytoolsapi.mindwired.com.br',
    'endpoints': {
        'ai': {
            'ask-gemini': {
                'url': '/api/ai/v1/ask-gemini?prompt=&image_url=&max_tokens=',
                'description': 'Ask a question to Gemini AI and get an answer. You can also provide an image to help the AI understand the context better, and set the maximum number of tokens to be generated.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 5,
            }
        },
        'randomizer': {
            'int-number': {
                'url': '/api/randomizer/v1/int-number?min=&max=',
                'description': 'Generates a random integer number between two numbers and returns it.',
                'rate_limit': get_rate_limit_message(5, 300, 18000, 30000),
                'cache_timeout': 1,
            },
            'float-number': {
                'url': '/api/randomizer/v1/float-number?min=&max=',
                'description': 'Generates a random float number between two numbers and returns it.',
                'rate_limit': get_rate_limit_message(5, 300, 18000, 30000),
                'cache_timeout': 1,
            }
        },
        'scraper': {
            'file-mediafire.com': {
                'url': '/api/scraper/v1/file-mediafire.com?id=',
                'description': 'Generates a direct and permanent link to a file hosted in "mediafire.com" and returns it.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
            },
            'file-drive.google.com': {
                'url': '/api/scraper/v1/file-drive.google.com?id=',
                'description': 'Generates a direct and temporary link to a file hosted in "drive.google.com" and returns it.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
            },
            'file-gofile.io': {
                'url': '/api/scraper/v1/file-gofile.io?id=',
                'description': 'Generates a direct and permanent link to a file hosted in "gofile.io" and returns it.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
            },
            'file-pillowcase.su': {
                'url': '/api/scraper/v1/file-pillowcase.su?id=',
                'description': 'Generates a direct and permanent link to a file hosted in "pillowcase.su" and returns it.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
            },
            'product-aliexpress.com': {
                'url': '/api/scraper/v1/product-aliexpress.com?id=',
                'description': 'Extracts accurate information from an existing product on "aliexpress.com" and returns it in an easy-to-understand JSON format.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
            },
            'video-youtube.com': {
                'url': '/api/scraper/v1/video-youtube.com?id=',
                'description': 'Extracts accurate information from an existing video on "youtube.com" and returns it in an easy-to-understand JSON format.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 14400,
            },
            'product-promotions': {
                'url': '/api/scraper/v1/product-promotions?name=',
                'description': 'Search for active promotions of a product in the main promotion sites and returns them in an easy-to-understand JSON format.',
                'rate_limit': get_rate_limit_message(1, 30, 200, 600),
                'cache_timeout': 300,
            }
        }
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
    return redirect('/endpoints', code=302)


@app.route('/endpoints', methods=['GET'])
@cache.cached(timeout=28800, make_cache_key=_make_cache_key)
def endpoints() -> tuple[dict, int]:
    return endpoints_data, 200


# Flask API routes
# Route: /api/ai/v?/ask-gemini
_data = endpoints_data['endpoints']['ai']['ask-gemini']
_route_ai__ask_gemini = _data['url'].split('?')[0] if '?' in _data['url'] else _data['url']
@app.route(_route_ai__ask_gemini, methods=['GET'])
@limiter.limit(_data['rate_limit'])
@cache.cached(timeout=_data['cache_timeout'], make_cache_key=_make_cache_key)
def _ai__ask_gemini() -> tuple[dict, int]:
    p_prompt = request.args.get('prompt')
    p_image_url = request.args.get('image_url')
    p_max_tokens = request.args.get('max_tokens')

    if not p_prompt:
        return get_error_response_message('The prompt parameter is required.'), 400

    if p_max_tokens and not p_max_tokens.isnumeric():
        return get_error_response_message('The max_tokens parameter must be an integer.'), 400

    output_data = ai__ask_gemini(gemini_api_keys, p_prompt, p_image_url, p_max_tokens)

    if output_data:
        return get_success_response_message(output_data['processing_time'], output_data['data'], _data['description']), 200
    else:
        return get_error_response_message('An error occurred while asking the question. Please check your query and try again.'), 404


# Route: /api/randomizer/v?/int-number
_data = endpoints_data['endpoints']['randomizer']['int-number']
_route_randomizer__int_number = _data['url'].split('?')[0] if '?' in _data['url'] else _data['url']
@app.route(_route_randomizer__int_number, methods=['GET'])
@limiter.limit(_data['rate_limit'])
@cache.cached(timeout=_data['cache_timeout'], make_cache_key=_make_cache_key)
def _randomizer__int_number() -> tuple[dict, int]:
    p_min = request.args.get('min')
    p_max = request.args.get('max')

    if not p_min or not p_min.isnumeric() or not p_max or not p_max.isnumeric():
        return get_error_response_message('The min and max parameters are required and must be integers.'), 400

    p_min, p_max = int(p_min), int(p_max)
    if p_min > p_max:
        return get_error_response_message('The min parameter must be less than the max parameter.'), 400

    output_data = randomizer__int_number(p_min, p_max)

    if output_data:
        return get_success_response_message(output_data['processing_time'], {'number': output_data['data']}, _data['description']), 200
    else:
        return get_error_response_message('An error occurred while generating the random number. Please check your query and try again.'), 404


# Route: /api/randomizer/v?/float-number
_ = endpoints_data['endpoints']['randomizer']['float-number']['url']
_route_randomizer__float_number = _.split('?')[0] if '?' in _ else _
@app.route(_route_randomizer__float_number, methods=['GET'])
@limiter.limit(endpoints_data['endpoints']['randomizer']['float-number']['rate_limit'])
@cache.cached(timeout=endpoints_data['endpoints']['randomizer']['float-number']['cache_timeout'], make_cache_key=_make_cache_key)
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
        return get_error_response_message('The min and max parameters are required and must be floats.'), 400

    p_min, p_max = float(p_min), float(p_max)
    if p_min > p_max:
        return get_error_response_message('The min parameter must be less than the max parameter.'), 400

    output_data = randomizer__float_number(float(p_min), float(p_max))

    if output_data:
        return get_success_response_message(output_data['processing_time'], {'number': output_data['data']}, endpoints_data['endpoints']['randomizer']['float-number']['description']), 200
    else:
        return get_error_response_message('An error occurred while generating the random number. Please check your query and try again.'), 404


# Route: /api/scraper/v?/file-mediafire.com
_ = endpoints_data['endpoints']['scraper']['file-mediafire.com']['url']
_route_scraper__file_mediafire0com = _.split('?')[0] if '?' in _ else _
@app.route(_route_scraper__file_mediafire0com, methods=['GET'])
@limiter.limit(endpoints_data['endpoints']['scraper']['file-mediafire.com']['rate_limit'])
@cache.cached(timeout=endpoints_data['endpoints']['scraper']['file-mediafire.com']['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__file_mediafire_com() -> tuple[dict, int]:
    p_id = request.args.get('id')

    if not p_id or not p_id.isalnum():
        return get_error_response_message('The id parameter is required and must be alphanumeric.'), 400

    output_data = scraper__file_mediafire0com(p_id)

    if output_data:
        return get_success_response_message(output_data['processing_time'], {'url': output_data['data']}, endpoints_data['endpoints']['scraper']['file-mediafire.com']['description']), 200
    else:
        return get_error_response_message('Query not found or invalid. Please check your query and try again.'), 404


# Route: /api/scraper/v?/file-drive.google.com
_ = endpoints_data['endpoints']['scraper']['file-drive.google.com']['url']
_route_scraper__file_drive0google0com = _.split('?')[0] if '?' in _ else _
@app.route(_route_scraper__file_drive0google0com, methods=['GET'])
@limiter.limit(endpoints_data['endpoints']['scraper']['file-drive.google.com']['rate_limit'])
@cache.cached(timeout=endpoints_data['endpoints']['scraper']['file-drive.google.com']['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__file_drive0google0com() -> tuple[dict, int]:
    p_id = request.args.get('id')

    if not p_id or not re_compile(r'^[a-zA-Z0-9_-]+$').match(p_id):
        return get_error_response_message('The id parameter is required and must be alphanumeric.'), 400

    output_data = scraper__file_drive0google0com(p_id)

    if output_data:
        return get_success_response_message(output_data['processing_time'], {'url': output_data['data']}, endpoints_data['endpoints']['scraper']['file-drive.google.com']['description']), 200
    else:
        return get_error_response_message('Query not found or invalid. Please check your query and try again.'), 404


# Route: /api/scraper/v?/file-gofile.io
_ = endpoints_data['endpoints']['scraper']['file-gofile.io']['url']
_route_scraper__file_gofile0io = _.split('?')[0] if '?' in _ else _
@app.route(_route_scraper__file_gofile0io, methods=['GET'])
@limiter.limit(endpoints_data['endpoints']['scraper']['file-gofile.io']['rate_limit'])
@cache.cached(timeout=endpoints_data['endpoints']['scraper']['file-gofile.io']['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__file_gofile0io() -> tuple[dict, int]:
    return _route_in_maintenance()

     # p_id = request.args.get('id')

     # if not p_id or not p_id.isalnum():
     #     return get_error_response_message('The id parameter is required and must be alphanumeric.'), 400

     # output_data = scraper__file_gofile0io(p_id)

     # if output_data:
     #     return get_success_response_message(output_data['processing_time'], {'url': output_data['data']}, endpoints_data['endpoints']['scraper']['file-gofile.io']['description']), 200
     # else:
     #     return get_error_response_message('Query not found or invalid. Please check your query and try again.'), 404


# Route: /api/scraper/v?/file-pillowcase.su
_ = endpoints_data['endpoints']['scraper']['file-pillowcase.su']['url']
_route_scraper__file_pillowcase0su = _.split('?')[0] if '?' in _ else _
@app.route(_route_scraper__file_pillowcase0su, methods=['GET'])
@limiter.limit(endpoints_data['endpoints']['scraper']['file-pillowcase.su']['rate_limit'])
@cache.cached(timeout=endpoints_data['endpoints']['scraper']['file-pillowcase.su']['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__file_pillowcase0su() -> tuple[dict, int]:
    p_id = request.args.get('id')

    if not p_id or not p_id.isalnum():
        return get_error_response_message('The id parameter is required and must be alphanumeric.'), 400

    output_data = scraper__file_pillowcase0su(p_id)

    if output_data:
        return get_success_response_message(output_data['processing_time'], {'url': output_data['data']}, endpoints_data['endpoints']['scraper']['file-pillowcase.su']['description']), 200
    else:
        return get_error_response_message('Query not found or invalid. Please check your query and try again.'), 404


# Route: /api/scraper/v?/product-aliexpress.com
_ = endpoints_data['endpoints']['scraper']['product-aliexpress.com']['url']
_route_scraper__product_aliexpress0com = _.split('?')[0] if '?' in _ else _
@app.route(_route_scraper__product_aliexpress0com, methods=['GET'])
@limiter.limit(endpoints_data['endpoints']['scraper']['product-aliexpress.com']['rate_limit'])
@cache.cached(timeout=endpoints_data['endpoints']['scraper']['product-aliexpress.com']['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__product_aliexpress0com() -> tuple[dict, int]:
    p_id = request.args.get('id')

    if not p_id or not p_id.isnumeric():
        return get_error_response_message('The id parameter is required and must be numeric.'), 400

    p_id = int(p_id)
    output_data = scraper__product_aliexpress0com(p_id)

    if output_data:
        return get_success_response_message(output_data['processing_time'], output_data['data'], endpoints_data['endpoints']['scraper']['product-aliexpress.com']['description']), 200
    else:
        return get_error_response_message('Query not found or invalid. Please check your query and try again.'), 404


# Route: /api/scraper/v?/video-youtube.com
_ = endpoints_data['endpoints']['scraper']['video-youtube.com']['url']
_route_scraper__video_youtube0com = _.split('?')[0] if '?' in _ else _
@app.route(_route_scraper__video_youtube0com, methods=['GET'])
@limiter.limit(endpoints_data['endpoints']['scraper']['video-youtube.com']['rate_limit'])
@cache.cached(timeout=endpoints_data['endpoints']['scraper']['video-youtube.com']['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__video_youtube0com() -> tuple[dict, int]:
    p_id = request.args.get('id')

    if not p_id or not re_compile(r'^[a-zA-Z0-9_-]+$').match(p_id):
        return get_error_response_message('The id parameter is required and must be alphanumeric.'), 400

    output_data = scraper__video_youtube0com(p_id)

    if output_data:
        return get_success_response_message(output_data['processing_time'], output_data['data'], endpoints_data['endpoints']['scraper']['video-youtube.com']['description']), 200
    else:
        return get_error_response_message('Query not found or invalid. Please check your query and try again.'), 404


# Route: /api/scraper/v?/product-promotions
_data = endpoints_data['endpoints']['scraper']['product-promotions']
_route_scraper__product_promotions = _data['url'].split('?')[0] if '?' in _data['url'] else _data['url']
@app.route(_route_scraper__product_promotions, methods=['GET'])
@limiter.limit(_data['rate_limit'])
@cache.cached(timeout=_data['cache_timeout'], make_cache_key=_make_cache_key)
def _scraper__product_promotions() -> tuple[dict, int]:
    p_name = request.args.get('name')

    if not p_name:
        return get_error_response_message('The name parameter is required.'), 400

    output_data = scraper__product_promotions(p_name)

    if output_data:
        return get_success_response_message(output_data['processing_time'], output_data['data'], _data['description']), 200
    else:
        return get_error_response_message('No active promotions were found for the chosen product. Please choose another product or change its name.'), 404


if __name__ == '__main__':
    app.config['JSON_SORT_KEYS'] = True
    app.run(debug=False, host='0.0.0.0', threaded=True, port=8452)
