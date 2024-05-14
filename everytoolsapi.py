import flask
from flask_caching import Cache
from pathlib import Path
from os import getenv
from http import HTTPStatus
from typing import *

from static.dependencies.version import APIVersion
from static.dependencies.functions import APITools, CacheFunctions
from static.dependencies.endpoints import Endpoints


app = flask.Flask(__name__)
app.app_context().push()

app.config['CACHE_TYPE'] = 'simple'
cache = Cache(app)

latest_api_version = APIVersion.Latest().version

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


@app.route('/', methods=['GET'], make_cache_key=CacheFunctions.cache_key)
@cache.cached(timeout=600)
def initial_page() -> Union[str, Any]:
    APITools.check_main_request(flask.request.remote_addr, None)
    return flask.render_template('index.html')


@app.route('/docs/', methods=['GET'], make_cache_key=CacheFunctions.cache_key)
@cache.cached(timeout=600)
def documentation_page() -> Union[str, Any]:
    APITools.check_main_request(flask.request.remote_addr, None)
    return flask.render_template('documentation.html')


@app.route('/api/', methods=['GET'], make_cache_key=CacheFunctions.cache_key)
@cache.cached(timeout=600)
def api() -> Union[Dict[str, Union[bool, str]], Any]:
    APITools.check_main_request(flask.request.remote_addr, None)
    return flask.redirect(f'/api/{latest_api_version}/status', code=302)


@app.route('/api/<version>/', methods=['GET'], make_cache_key=CacheFunctions.cache_key)
@cache.cached(timeout=600)
def api_version(version: str) -> Union[Dict[str, Union[bool, str]], Any]:
    APITools.check_main_request(flask.request.remote_addr, None)
    return flask.redirect(f'/api/{version}/status', code=302)


@app.route('/api/<version>/status/', methods=['GET'], make_cache_key=CacheFunctions.cache_key)
@cache.cached(timeout=600)
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
