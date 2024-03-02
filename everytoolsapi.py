from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from dotenv import dotenv_values
from re import compile as re_compile
from typing import Any

from api_resources.main_endpoints.url_generator.v1.mediafire_file import main as url_generator__mediafire_file
from api_resources.main_endpoints.url_generator.v1.googledrive_file import main as url_generator__googledrive_file
from api_resources.main_endpoints.url_generator.v1.gofile_file import main as url_generator__gofile_file

from api_resources.main_endpoints.wrapper.v1.aliexpress_product import main as wrapper__aliexpress
from api_resources.main_endpoints.wrapper.v1.yotube_video import main as wrapper__youtube_video

from api_resources.main_endpoints.randomizer.v1.random_int_number import main as randomizer__random_int_number
from api_resources.main_endpoints.randomizer.v1.random_float_number import main as randomizer__random_float_number

from api_resources.main_endpoints.ai.v1.ask_to_gemini import main as ai__ask_to_gemini


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


# Flask required functions
def _make_cache_key(*args, **kwargs) -> str:
    return f'{request.url}{str(request.args)}'


def _route_in_maintenance() -> jsonify:
    return jsonify({'success': False, 'message': 'This endpoint is under maintenance. Please try again later.'}), 503


# Flask error handlers
@app.errorhandler(404)
@cache.cached(timeout=86400, make_cache_key=_make_cache_key)
def weberror_404(_) -> jsonify:
    return jsonify({'success': False, 'message': 'The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.'}), 404


@app.errorhandler(429)
@cache.cached(timeout=86400, make_cache_key=_make_cache_key)
def weberror_429(_) -> jsonify:
    return jsonify({'success': False, 'message': 'You have exceeded the rate limit! Please wait a few seconds and try again.'}), 429


# Flask general routes
@app.route('/')
@cache.cached(timeout=86400, make_cache_key=_make_cache_key)
def home() -> jsonify:
    return jsonify({
        'message': 'Welcome to the EveryTools API. Where you can find all the tools you need in one place.',
        'author_github': 'https://github.com/Henrique-Coder',
        'source_code_url': 'https://github.com/Henrique-Coder/everytools-api',
        'base_url': 'http://node1.mindwired.com.br:8452',
        'endpoints': {
            'url-generator': {
                'mediafire': {
                    'url': '/api/url-generator/v1/mediafire-file?id=',
                    'description': 'Generates a direct download link for a file hosted on MediaFire.',
                    'rate_limit': '1/second;30/minute;200/hour;600/day',
                },
                'googledrive': {
                    'url': '/api/url-generator/v1/googledrive-file?id=',
                    'description': 'Generates a direct download link for a file hosted on Google Drive.',
                    'rate_limit': '1/second;30/minute;200/hour;600/day',
                },
                'gofile': {
                    'url': '/api/url-generator/v1/gofile-file?id=',
                    'description': 'Generates a direct download link for a file hosted on Gofile.',
                    'rate_limit': '1/second;30/minute;200/hour;600/day',
                }
            },
            'wrapper': {
                'aliexpress-product': {
                    'url': '/api/wrapper/v1/aliexpress-product?id=',
                    'description': 'Wraps AliExpress product info into a friendly JSON format.',
                    'rate_limit': '1/second;30/minute;200/hour;600/day',
                },
                'youtube-video': {
                    'url': '/api/wrapper/v1/youtube-video?id=',
                    'description': 'Wraps YouTube video info into a friendly JSON format.',
                    'rate_limit': '1/second;30/minute;200/hour;600/day',
                }
            },
            'randomizer': {
                'random-int-number': {
                    'url': '/api/randomizer/v1/random-int-number?min=&max=',
                    'description': 'Generates a random integer number between two numbers.',
                    'rate_limit': '5/second;5000/day',
                },
                'random-float-number': {
                    'url': '/api/randomizer/v1/random-float-number?min=&max=',
                    'description': 'Generates a random float number between two numbers.',
                    'rate_limit': '5/second;5000/day',
                }
            },
            'ai': {
                'ask-to-gemini': {
                    'url': '/api/ai/v1/ask-to-gemini?prompt=&image_url=&max_tokens=',
                    'description': 'Ask a question to Gemini AI and get an answer.',
                    'rate_limit': '1/second;30/minute;200/hour;400/day',
                }
            }
        }
    }), 200


# Flask API routes
# Route: /api/url-generator/mediafire-file -> Generates a direct download link for a file hosted on MediaFire.
@app.route('/api/url-generator/v1/mediafire-file', methods=['GET'])
@limiter.limit('1/second;30/minute;200/hour;600/day')
@cache.cached(timeout=300, make_cache_key=_make_cache_key)
def _url_generator__mediafire_file() -> jsonify:
    p_id = request.args.get('id')

    if not p_id or not p_id.isalnum():
        return jsonify({'success': False, 'message': "The id parameter is required and must be alphanumeric."}), 400

    output_data = url_generator__mediafire_file(p_id)

    if output_data:
        return jsonify({'success': True, 'output': {'url': output_data}, 'query': {'id': p_id}}), 200
    else:
        return jsonify({'success': False, 'message': 'Query not found or invalid. Please check your query and try again.', 'query': {'id': p_id}}), 404


# Route: /api/url-generator/googledrive-file -> Generates a direct download link for a file hosted on Google Drive
@app.route('/api/url-generator/v1/googledrive-file', methods=['GET'])
@limiter.limit('1/second;30/minute;200/hour;600/day')
@cache.cached(timeout=300, make_cache_key=_make_cache_key)
def _url_generator__googledrive_file() -> jsonify:
    p_id = request.args.get('id')

    if not p_id or not re_compile(r'^[a-zA-Z0-9_-]+$').match(p_id):
        return jsonify({'success': False, 'message': "The id parameter is required and must be alphanumeric."}), 400

    output_data = url_generator__googledrive_file(p_id)

    if output_data:
        return jsonify({'success': True, 'output': {'url': output_data}, 'query': {'id': p_id}}), 200
    else:
        return jsonify({'success': False, 'message': 'Query not found or invalid. Please check your query and try again.', 'query': {'id': p_id}}), 404


# Route: /api/url-generator/gofile-file -> Generates a direct download link for a file hosted on Gofile
@app.route('/api/url-generator/v1/gofile-file', methods=['GET'])
@limiter.limit('1/second;30/minute;200/hour;600/day')
@cache.cached(timeout=300, make_cache_key=_make_cache_key)
def _url_generator__gofile_file() -> jsonify:
    return _route_in_maintenance()

    p_id = request.args.get('id')

    if not p_id or not p_id.isalnum():
        return jsonify({'success': False, 'message': "The id parameter is required and must be alphanumeric."}), 400

    output_data = url_generator__gofile_file(p_id)

    if output_data:
        return jsonify({'success': True, 'output': {'url': output_data}, 'query': {'id': p_id}}), 200
    else:
        return jsonify({'success': False, 'message': 'Query not found or invalid. Please check your query and try again.', 'query': {'id': p_id}}), 404


# Route: /api/wrapper/aliexpress-product -> Wraps AliExpress product info into a friendly JSON format
@app.route('/api/wrapper/v1/aliexpress-product', methods=['GET'])
@limiter.limit('1/second;30/minute;200/hour;600/day')
@cache.cached(timeout=300, make_cache_key=_make_cache_key)
def _wrapper__aliexpress_product() -> jsonify:
    p_id = request.args.get('id')

    if not p_id or not p_id.isnumeric():
        return jsonify({'success': False, 'message': "The id parameter is required and must be numeric."}), 400

    p_id = int(p_id)
    output_data = wrapper__aliexpress(p_id)

    if output_data:
        return jsonify({'success': True, 'output': {'data': output_data}, 'query': {'id': p_id}}), 200
    else:
        return jsonify({'success': False, 'message': 'Query not found or invalid. Please check your query and try again.', 'query': {'id': p_id}}), 404


# Route: /api/wrapper/youtube-video -> Wraps YouTube video info into a friendly JSON format
@app.route('/api/wrapper/v1/youtube-video', methods=['GET'])
@limiter.limit('1/second;30/minute;200/hour;600/day')
@cache.cached(timeout=21600, make_cache_key=_make_cache_key)
def _wrapper__youtube_video() -> jsonify:
    p_id = request.args.get('id')

    if not p_id or not re_compile(r'^[a-zA-Z0-9_-]+$').match(p_id):
        return jsonify({'success': False, 'message': "The id parameter is required and must be alphanumeric."}), 400

    output_data = wrapper__youtube_video(p_id)

    if output_data:
        return jsonify({'success': True, 'output': {'data': output_data}, 'query': {'id': p_id}}), 200
    else:
        return jsonify({'success': False, 'message': 'Query not found or invalid. Please check your query and try again.', 'query': {'id': p_id}}), 404


# Route: /api/randomizer/random-int-number -> Generates a random integer number between two numbers
@app.route('/api/randomizer/v1/random-int-number', methods=['GET'])
@limiter.limit('5/second;5000/day')
def _randomizer__random_int_number() -> jsonify:
    p_min = request.args.get('min')
    p_max = request.args.get('max')

    if not p_min or not p_min.isnumeric() or not p_max or not p_max.isnumeric():
        return jsonify({'success': False, 'message': "The min and max parameters are required and must be integers."}), 400

    p_min, p_max = int(p_min), int(p_max)
    if p_min > p_max:
        return jsonify({'success': False, 'message': "The min parameter must be less than the max parameter."}), 400

    output_data = randomizer__random_int_number(p_min, p_max)

    if output_data:
        return jsonify({'success': True, 'number': output_data, 'type': 'int', 'query': {'min': p_min, 'max': p_max}}), 200
    else:
        return jsonify({'success': False, 'message': 'An error occurred while generating the random number. Please check your query and try again.', 'query': {'min': p_min, 'max': p_max}}), 404


# Route: /api/randomizer/random-float-number -> Generates a random float number between two numbers
@app.route('/api/randomizer/v1/random-float-number', methods=['GET'])
@limiter.limit('5/second;5000/day')
def _randomizer__random_float_number() -> jsonify:
    def is_float(value: Any) -> bool:
        try:
            float(value)
            return True
        except Exception:
            return False

    p_min = request.args.get('min')
    p_max = request.args.get('max')

    if not p_min or not is_float(p_min) or not p_max or not is_float(p_max):
        return jsonify({'success': False, 'message': "The min and max parameters are required and must be floats."}), 400

    p_min, p_max = float(p_min), float(p_max)
    if p_min > p_max:
        return jsonify({'success': False, 'message': "The min parameter must be less than the max parameter."}), 400

    output_data = randomizer__random_float_number(float(p_min), float(p_max))

    if output_data:
        return jsonify({'success': True, 'number': output_data, 'type': 'float', 'query': {'min': p_min, 'max': p_max}}), 200
    else:
        return jsonify({'success': False, 'message': 'An error occurred while generating the random number. Please check your query and try again.', 'query': {'min': p_min, 'max': p_max}}), 404


# Route: /api/ai/ask-to-gemini -> Ask a question to Gemini AI and get an answer
@app.route('/api/ai/v1/ask-to-gemini', methods=['GET'])
@limiter.limit('1/second;30/minute;200/hour;400/day')
@cache.cached(timeout=300, make_cache_key=_make_cache_key)
def _ai__ask_to_gemini() -> jsonify:
    p_prompt = request.args.get('prompt')
    p_image_url = request.args.get('image_url')
    p_max_tokens = request.args.get('max_tokens')

    if not p_prompt:
        return jsonify({'success': False, 'message': "The prompt parameter is required."}), 400

    if p_max_tokens and not p_max_tokens.isnumeric():
        return jsonify({'success': False, 'message': "The max_tokens parameter must be an integer."}), 400

    output_data = ai__ask_to_gemini(gemini_api_keys, p_prompt, p_image_url, p_max_tokens)

    if output_data:
        return jsonify({'success': True, 'output': output_data, 'query': {'prompt': p_prompt, 'image_url': p_image_url}}), 200
    else:
        return jsonify({'success': False, 'message': 'An error occurred while asking the question. Please check your query and try again.', 'query': {'prompt': p_prompt, 'image_url': p_image_url}}), 404


if __name__ == '__main__':
    app.config['JSON_SORT_KEYS'] = True
    app.run(debug=False, host='0.0.0.0', threaded=True, port=8452)
