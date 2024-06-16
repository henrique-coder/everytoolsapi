from flask import Flask, jsonify, request, render_template
from flask_limiter import util as flask_limiter_utils, Limiter
from flask_caching import Cache
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from flask_compress import Compress
from logging.config import dictConfig
from dotenv import load_dotenv
from os import getenv
from yaml import safe_load as yaml_safe_load
from pathlib import Path
from typing import *

from static.data.version import APIVersion
from static.data.functions import APITools, LimiterTools, CacheTools
from static.data.endpoints import APIEndpoints


# Load the environment variables
load_dotenv()

# Configuration class
class Config:
    def __init__(self, **entries: Dict[str, Any]) -> None:
        for key, value in entries.items():
            if isinstance(value, dict):
                value = Config(**value)

            self.__dict__[key] = value


# Setup Flask application
app = Flask(__name__)

# Setup Flask logging configuration
logging_config = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        },
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
}
dictConfig(logging_config)

# Setup Redis URL
redis_host = getenv('REDIS_HOST')
redis_port = int(getenv('REDIS_PORT'))
redis_db = int(getenv('REDIS_DB'))
redis_username = getenv('REDIS_USERNAME')
redis_password = getenv('REDIS_PASSWORD')
redis_url = f'redis://{redis_username}:{redis_password}@{redis_host}:{redis_port}/{redis_db}'

# Setup Flask limiter with Redis
limiter = Limiter(flask_limiter_utils.get_remote_address, app=app, storage_uri=redis_url)

# Setup Flask cache with Redis
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_HOST'] = redis_host
app.config['CACHE_REDIS_PORT'] = redis_port
app.config['CACHE_REDIS_DB'] = redis_db
app.config['CACHE_REDIS_USERNAME'] = redis_username
app.config['CACHE_REDIS_PASSWORD'] = redis_password
app.config['CACHE_REDIS_URL'] = redis_url
cache = Cache(app)

# Setup Talisman for security headers (with custom options), CSRF protection and Compress for response compression
talisman = Talisman(app, content_security_policy={'default-src': ["'self'", 'https://cdnjs.cloudflare.com'], 'style-src': ["'self'", "'unsafe-inline'", 'https://cdnjs.cloudflare.com'], 'script-src': ["'self'", 'https://cdnjs.cloudflare.com']})
csrf = CSRFProtect(app)
compression = Compress(app)


# Setup main routes
@app.route('/', methods=['GET'])
@limiter.limit(LimiterTools.gen_ratelimit_message(per_min=60))
@cache.cached(timeout=300, make_cache_key=CacheTools.gen_cache_key)
def initial_page() -> render_template:
    return render_template('index.html')


# Setup API routes
_parser__useragent = APIEndpoints.v2.parser.useragent
@app.route(f'/api/<query_version>{_parser__useragent.endpoint_url}', methods=_parser__useragent.allowed_methods)
@limiter.limit(_parser__useragent.ratelimit)
@cache.cached(timeout=_parser__useragent.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def parser__useragent(query_version: str) -> jsonify:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    return jsonify(_parser__useragent.run(APITools.extract_request_data(request)))


_parser__url = APIEndpoints.v2.parser.url
@app.route(f'/api/<query_version>{_parser__url.endpoint_url}', methods=_parser__url.allowed_methods)
@limiter.limit(_parser__url.ratelimit)
@cache.cached(timeout=_parser__url.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def parser__url(query_version: str) -> jsonify:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    return jsonify(_parser__url.run(APITools.extract_request_data(request)))


_parser__time_hms = APIEndpoints.v2.parser.sec_to_hms
@app.route(f'/api/<query_version>{_parser__time_hms.endpoint_url}', methods=_parser__time_hms.allowed_methods)
@limiter.limit(_parser__time_hms.ratelimit)
@cache.cached(timeout=_parser__time_hms.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def parser__time_hms(query_version: str) -> jsonify:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    return jsonify(_parser__time_hms.run(APITools.extract_request_data(request)))


_parser__email = APIEndpoints.v2.parser.email
@app.route(f'/api/<query_version>{_parser__email.endpoint_url}', methods=_parser__email.allowed_methods)
@limiter.limit(_parser__email.ratelimit)
@cache.cached(timeout=_parser__email.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def parser__email(query_version: str) -> jsonify:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    return jsonify(_parser__email.run(APITools.extract_request_data(request)))


_parser__text_counter = APIEndpoints.v2.parser.text_counter
@app.route(f'/api/<query_version>{_parser__text_counter.endpoint_url}', methods=_parser__text_counter.allowed_methods)
@limiter.limit(_parser__text_counter.ratelimit)
@cache.cached(timeout=_parser__text_counter.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def parser__text_counter(query_version: str) -> jsonify:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    return jsonify(_parser__text_counter.run(APITools.extract_request_data(request)))


_tools__text_lang_detector = APIEndpoints.v2.tools.text_lang_detector
@app.route(f'/api/<query_version>{_tools__text_lang_detector.endpoint_url}', methods=_tools__text_lang_detector.allowed_methods)
@limiter.limit(_tools__text_lang_detector.ratelimit)
@cache.cached(timeout=_tools__text_lang_detector.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def tools__text_lang_detector(query_version: str) -> jsonify:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    return jsonify(_tools__text_lang_detector.run(APITools.extract_request_data(request)))


_tools__text_translator = APIEndpoints.v2.tools.text_translator
@app.route(f'/api/<query_version>{_tools__text_translator.endpoint_url}', methods=_tools__text_translator.allowed_methods)
@limiter.limit(_tools__text_translator.ratelimit)
@cache.cached(timeout=_tools__text_translator.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def tools__text_translator(query_version: str) -> jsonify:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    return jsonify(_tools__text_translator.run(APITools.extract_request_data(request)))


_scraper__google_search = APIEndpoints.v2.scraper.google_search
@app.route(f'/api/<query_version>{_scraper__google_search.endpoint_url}', methods=_scraper__google_search.allowed_methods)
@limiter.limit(_scraper__google_search.ratelimit)
@cache.cached(timeout=_scraper__google_search.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def scraper__google_search(query_version: str) -> jsonify:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    return jsonify(_scraper__google_search.run(APITools.extract_request_data(request)))


_scraper__instagram_reels = APIEndpoints.v2.scraper.instagram_reels
@app.route(f'/api/<query_version>{_scraper__instagram_reels.endpoint_url}', methods=_scraper__instagram_reels.allowed_methods)
@limiter.limit(_scraper__instagram_reels.ratelimit)
@cache.cached(timeout=_scraper__instagram_reels.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def scraper__instagram_reels(query_version: str) -> jsonify:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    return jsonify(_scraper__instagram_reels.run(APITools.extract_request_data(request)))


_scraper__youtube_media = APIEndpoints.v2.scraper.youtube_media
@app.route(f'/api/<query_version>{_scraper__youtube_media.endpoint_url}', methods=_scraper__youtube_media.allowed_methods)
@limiter.limit(_scraper__youtube_media.ratelimit)
@cache.cached(timeout=_scraper__youtube_media.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def scraper__youtube_media(query_version: str) -> jsonify:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    return jsonify(_scraper__youtube_media.run(APITools.extract_request_data(request)))


if __name__ == '__main__':
    # Load the configuration file
    current_path = Path(__file__).parent
    config_path = Path(current_path, 'config.yml')
    config = Config(**yaml_safe_load(config_path.open('r')))

    # Setting up Flask default configuration
    app.static_folder = Path(current_path, config.flask.staticFolder)
    app.template_folder = Path(current_path, config.flask.templateFolder)

    # Run the web server with the specified configuration
    app.run(debug=False, host=config.flask.host, port=config.flask.port, threaded=config.flask.threadedServer)
