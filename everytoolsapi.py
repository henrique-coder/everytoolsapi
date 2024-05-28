import flask
from flask_caching import Cache
from flask_swagger_ui import get_swaggerui_blueprint
from pathlib import Path
from os import getenv
from http import HTTPStatus
from typing import *

from static.dependencies.version import APIVersion
from static.dependencies.functions import APITools, CacheFunctions
from static.dependencies.endpoints import Endpoints


# Flask application
app = flask.Flask(__name__)
app.app_context().push()

app.config['CACHE_TYPE'] = 'simple'
cache = Cache(app)

# Get the latest API version
latest_api_version = APIVersion.Latest().version

# Swagger UI
SWAGGER_URL = f'/api/{latest_api_version}/docs/'
SWAGGER_API_URL = f'/api/swagger/data.json'
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, SWAGGER_API_URL, config={'app_name': 'EveryTools API'})
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

google_gemini_api_keys = list()
start_number = 0
while True:
    start_number += 1
    value = getenv(f'GOOGLE_GEMINI_API_KEY_{start_number}')
    if value: google_gemini_api_keys.append(str(value))
    else: break


def show_error_page(error_code: int, custom_error_name: str = None):
    if not custom_error_name:
        error_name = HTTPStatus(error_code).phrase
        custom_error_name = error_name

    return flask.render_template('web_errors.html', error_code=error_code, error_name=custom_error_name), error_code


@app.errorhandler(404)
@cache.cached(timeout=86400, make_cache_key=CacheFunctions.cache_key)
def error_404(e: Exception) -> Tuple[str, int]: return show_error_page(404)


@app.errorhandler(429)
@cache.cached(timeout=86400, make_cache_key=CacheFunctions.cache_key)
def error_429(e: Exception) -> Tuple[str, int]: return show_error_page(429)


@app.errorhandler(500)
@cache.cached(timeout=86400, make_cache_key=CacheFunctions.cache_key)
def error_500(e: Exception) -> Tuple[str, int]: return show_error_page(500)


@app.errorhandler(503)
@cache.cached(timeout=86400, make_cache_key=CacheFunctions.cache_key)
def error_503(e: Exception) -> Tuple[str, int]: return show_error_page(503)


@app.route(SWAGGER_API_URL, methods=['GET'])
@cache.cached(timeout=600, make_cache_key=CacheFunctions.cache_key)
def create_swagger_spec() -> Any:
    APITools.check_main_request(flask.request.remote_addr, None)
    swag_data = {
        'swagger': '2.0',
        'info': {
            'title': 'EveryTools API',
            'description': 'Welcome to the EveryTools API. Where you can find all the tools you need in one place.',
            'version': latest_api_version,
            'contact': {
                'name': 'Henrique-Coder',
                'url': 'https://henrique-coder.mindwired.com.br',
                'email': 'henriquemoreira10fk@gmail.com',
            },
            'license': {
                'name': 'MIT License',
                'url': 'https://github.com/Henrique-Coder/everytoolsapi/blob/main/LICENSE',
            }
        },
        'servers': [
            {
                'url': 'https://everytoolsapi-henrique-coder.koyeb.app/api/v2',
                'description': 'Production Server'
            },
        ],
        'paths': {
            f'/api/{latest_api_version}/randomizer/int-number': {
                'get': {
                    'description': 'Randomize an integer number',
                    'parameters': [
                        {
                            'name': 'min',
                            'in': 'query',
                            'description': 'Minimum number',
                            'required': True,
                            'type': 'integer',
                        },
                        {
                            'name': 'max',
                            'in': 'query',
                            'description': 'Maximum number',
                            'required': True,
                            'type': 'integer',
                        },
                    ],
                    'responses': {
                        '200': {
                            'description': 'A random integer number',
                        }
                    }
                }
            },
            f'/api/{latest_api_version}/randomizer/float-number': {
                'get': {
                    'description': 'Randomize a float number',
                    'parameters': [
                        {
                            'name': 'min',
                            'in': 'query',
                            'description': 'Minimum number',
                            'required': True,
                            'type': 'number',
                        },
                        {
                            'name': 'max',
                            'in': 'query',
                            'description': 'Maximum number',
                            'required': True,
                            'type': 'number',
                        },
                    ],
                    'responses': {
                        '200': {
                            'description': 'A random float number',
                        }
                    }
                }
            },
            f'/api/{latest_api_version}/parser/user-agent': {
                'get': {
                    'description': 'Parse your current or a custom user agent string',
                    'parameters': [
                        {
                            'name': 'query',
                            'in': 'query',
                            'description': 'User agent string',
                            'required': False,
                            'type': 'string',
                        },
                    ],
                    'responses': {
                        '200': {
                            'description': 'Parsed user agent string',
                        }
                    }
                }
            },
            f'/api/{latest_api_version}/requester/ip-address': {
                'get': {
                    'description': 'Fetch information about your current or a custom IP address',
                    'parameters': [
                        {
                            'name': 'query',
                            'in': 'query',
                            'description': 'IP address',
                            'required': False,
                            'type': 'string',
                        },
                    ],
                    'responses': {
                        '200': {
                            'description': 'IP address',
                        }
                    }
                }
            },
            f'/api/{latest_api_version}/scraper/media-youtube.com': {
                'get': {
                    'description': 'Scrape information from a YouTube media URL',
                    'parameters': [
                        {
                            'name': 'query',
                            'in': 'query',
                            'description': 'YouTube media URL',
                            'required': True,
                            'type': 'string',
                        },
                    ],
                    'responses': {
                        '200': {
                            'description': 'Detailed information about the YouTube media URL',
                        }
                    }
                }
            },
        }
    }

    return flask.jsonify(swag_data)


@app.route('/', methods=['GET'])
@cache.cached(timeout=600, make_cache_key=CacheFunctions.cache_key)
def initial_page() -> Union[str, Any]:
    APITools.check_main_request(flask.request.remote_addr, None)
    return flask.render_template('index.html')


@app.route('/docs/', methods=['GET'])
@cache.cached(timeout=600, make_cache_key=CacheFunctions.cache_key)
def documentation_page() -> Union[str, Any]:
    APITools.check_main_request(flask.request.remote_addr, None)
    return flask.redirect(f'/api/{latest_api_version}/docs/', code=302)


@app.route('/api/', methods=['GET'])
@cache.cached(timeout=600, make_cache_key=CacheFunctions.cache_key)
def api() -> Union[Dict[str, Union[bool, str]], Any]:
    APITools.check_main_request(flask.request.remote_addr, None)
    return flask.redirect(f'/api/{latest_api_version}/status', code=302)


@app.route('/api/<version>/', methods=['GET'])
@cache.cached(timeout=600, make_cache_key=CacheFunctions.cache_key)
def api_version(version: str) -> Union[Dict[str, Union[bool, str]], Any]:
    APITools.check_main_request(flask.request.remote_addr, None)
    return flask.redirect(f'/api/{version}/status', code=302)


@app.route('/api/<version>/status/', methods=['GET'])
@cache.cached(timeout=600, make_cache_key=CacheFunctions.cache_key)
def api_version_status(version: str) -> Union[Dict[str, Union[bool, str]], Any]:
    APITools.check_main_request(flask.request.remote_addr, None)
    return Endpoints.api_version(version).get_status(version)


info_randomizer_int_number = Endpoints.V2.Randomizer.int_number.info
@app.route(f'/api/<version>/randomizer/int-number/', methods=info_randomizer_int_number['methods'])
@cache.cached(timeout=info_randomizer_int_number['cache'], make_cache_key=CacheFunctions.cache_key)
def randomizer_int_number(version: str) -> Any:
    APITools.check_main_request(flask.request.remote_addr, info_randomizer_int_number['ratelimit'], version, latest_api_version)
    return Endpoints.api_version(version).Randomizer.int_number.run({'min': flask.request.args.get('min'), 'max': flask.request.args.get('max')})


info_randomizer_float_number = Endpoints.V2.Randomizer.float_number.info
@app.route('/api/<version>/randomizer/float-number/', methods=info_randomizer_float_number['methods'])
@cache.cached(timeout=info_randomizer_float_number['cache'], make_cache_key=CacheFunctions.cache_key)
def randomizer_float_number(version: str) -> Any:
    APITools.check_main_request(flask.request.remote_addr, info_randomizer_float_number['ratelimit'], version, latest_api_version)
    return Endpoints.api_version(version).Randomizer.float_number.run({'min': flask.request.args.get('min'), 'max': flask.request.args.get('max')})


info_parser_user_agent = Endpoints.V2.Parser.user_agent.info
@app.route('/api/<version>/parser/user-agent/', methods=info_parser_user_agent['methods'])
@cache.cached(timeout=info_parser_user_agent['cache'], make_cache_key=CacheFunctions.cache_key)
def parser_user_agent(version: str) -> Any:
    APITools.check_main_request(flask.request.remote_addr, info_parser_user_agent['ratelimit'], version, latest_api_version)
    return Endpoints.api_version(version).Parser.user_agent.run({'remoteUserAgentHeader': flask.request.user_agent.string, 'query': flask.request.args.get('query')})


info_requester_ip_address = Endpoints.V2.Requester.ip_address.info
@app.route('/api/<version>/requester/ip-address/', methods=info_requester_ip_address['methods'])
@cache.cached(timeout=info_requester_ip_address['cache'], make_cache_key=CacheFunctions.cache_key)
def requester_ip_address(version: str) -> Any:
    APITools.check_main_request(flask.request.remote_addr, info_requester_ip_address['ratelimit'], version, latest_api_version)
    return Endpoints.api_version(version).Requester.ip_address.run({'remoteIpAddressHeader': flask.request.remote_addr, 'query': flask.request.args.get('query')})


info_scraper_media_youtube_com = Endpoints.V2.Scraper.media_youtube_com.info
@app.route('/api/<version>/scraper/media-youtube.com/', methods=info_scraper_media_youtube_com['methods'])
@cache.cached(timeout=info_scraper_media_youtube_com['cache'], make_cache_key=CacheFunctions.cache_key)
def scraper_media_youtube_com(version: str) -> Any:
    APITools.check_main_request(flask.request.remote_addr, info_scraper_media_youtube_com['ratelimit'], version, latest_api_version)
    return Endpoints.api_version(version).Scraper.media_youtube_com.run({'query': flask.request.args.get('query')})


if __name__ == '__main__':
    app.config['JSON_SORT_KEYS'] = True
    app.template_folder = Path(Path.cwd(), 'templates').resolve()
    app.run(host='0.0.0.0', port=13579, threaded=True, load_dotenv=True, debug=False)
