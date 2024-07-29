# Built-in modules
from base64 import b64decode
from http import HTTPStatus
from os import getenv
from pathlib import Path
from platform import system as get_os_name
from typing import Any, Dict, Tuple
from zlib import decompress as zlib_decompress

# Third-party modules
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, redirect
from flask_caching import Cache
from flask_compress import Compress
from flask_cors import CORS
from flask_limiter import util as flask_limiter_utils, Limiter
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from yaml import safe_load as yaml_safe_load

# Local modules
from static.data.databases import APIRequestLogs
from static.data.endpoints import APIEndpoints
from static.data.functions import APITools, LimiterTools, CacheTools
from static.data.logger import logger
from static.data.version import APIVersion


# Configuration class
class Config:
    def __init__(self, **entries: Dict[str, Any]) -> None:
        for key, value in entries.items():
            if isinstance(value, dict):
                value = Config(**value)

            self.__dict__[key] = value


# Setup Flask application and debugging mode
app = Flask(__name__)

# Load the environment variables
production_env_path = Path(Path(__file__).parent, '.env')
development_env_path = Path(Path(__file__).parent, '.dev.env')
logger.info('Environment variables loaded successfully')

# If the operating system is Windows, enable debugging mode, otherwise disable it
if get_os_name() == 'Windows':
    logger.info('Running on Windows, enabling debugging mode')
    debugging_mode = True
else:
    logger.info('Running on a non-Windows operating system, disabling debugging mode')
    debugging_mode = False

# Load the environment variables based on the debugging mode
if not debugging_mode:
    if Path(production_env_path).exists(): load_dotenv(dotenv_path=production_env_path)
    else: load_dotenv()
else:
    if Path(development_env_path).exists(): load_dotenv(dotenv_path=development_env_path)
    else: logger.error(f'No environment file found at "{development_env_path}"')

# Setup Redis configuration
redis_username = getenv('REDIS_USERNAME')
redis_password = getenv('REDIS_PASSWORD')
redis_host = getenv('REDIS_HOST')
redis_port = int(getenv('REDIS_PORT'))
redis_db = int(getenv('REDIS_DB'))
redis_url = f'redis://{redis_username}:{redis_password}@{redis_host}:{redis_port}/{redis_db}'
logger.info('Redis server configuration loaded successfully')

# Setup Flask limiter with Redis
limiter = Limiter(flask_limiter_utils.get_remote_address, app=app, storage_uri=redis_url)
logger.info('Flask limiter successfully initialized')

# Setup Flask cache with Redis
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_HOST'] = redis_host
app.config['CACHE_REDIS_PORT'] = redis_port
app.config['CACHE_REDIS_DB'] = redis_db
app.config['CACHE_REDIS_USERNAME'] = redis_username
app.config['CACHE_REDIS_PASSWORD'] = redis_password
cache = Cache(app)
logger.info('Flask cache successfully initialized')

# Setup Talisman for security headers
talisman = Talisman(app, content_security_policy={'default-src': ["'self'", 'https://cdnjs.cloudflare.com'], 'style-src': ["'self'", "'unsafe-inline'", 'https://cdnjs.cloudflare.com'], 'script-src': ["'self'", 'https://cdnjs.cloudflare.com']})
logger.info('Talisman successfully initialized')

# Setup CSRF protection
csrf = CSRFProtect(app)
logger.info('CSRF protection successfully initialized')

# Setup response compression
compression = Compress(app)
logger.info('Response compression successfully initialized')

# Setup CORS
cors = CORS(app, resources={r'/api/*': {'origins': '*'}})
logger.info('CORS successfully initialized')

# Setup proxy fix for the Flask application
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Setup PostgreSQL configuration
postgresql_username = getenv('POSTGRESQL_USERNAME')
postgresql_password = getenv('POSTGRESQL_PASSWORD')
postgresql_db_name = getenv('POSTGRESQL_DB_NAME')
postgresql_host = getenv('POSTGRESQL_HOST')
postgresql_port = getenv('POSTGRESQL_PORT')
postgresql_ssl_mode = getenv('POSTGRESQL_SSL_MODE')
postgresql_url = f'postgresql://{postgresql_username}:{postgresql_password}@{postgresql_host}:{postgresql_port}/{postgresql_db_name}?sslmode={postgresql_ssl_mode}'
logger.info('PostgreSQL server configuration loaded successfully')

# Initialize the database connection (PostgreSQL) and create the required tables
db_client = APIRequestLogs()
db_client.connect(postgresql_db_name, postgresql_username, postgresql_password, postgresql_host, postgresql_port, postgresql_ssl_mode)
db_client.create_required_tables()
logger.info('PostgreSQL database connection initialized successfully')

# Setup and decompress the favicon base64 data
compressed_favicon_base64_data = r'eNrtllt3qjwQhn+QF+DZXk4gnFQgCCreVbpFQUU8NC2//ptE7aZddn93e980a02SWXky7yQkrAAAAaBgawCi1UArRNdIsdJEBbJicB+/FwafCxUVuXvPpYPzyEAV/WOEAc0hWJfnKfrLpQrp4cUHW3cVDjB7ToDveY6CscLJy6GVg9qOFzg+Rt89KwNQ9+gDCTYYNYoLCJeZgj7nnBT8dQBg7wswX4fIL8oZBnVWYrynMnLhrymw8rV5jQ/w62zD/Lh8A3237mG8nY/zrWOA46IHL0kKueOav3kK6jxZ1vP5HR/nr8T81wnyC8k/2ZjfXgF7Np2gvxP5WdVt/Db/qofxNaj82/rosFqBRrfqAPdkewJnwhgnwXFOYXIkbRive3aqNdMNh6TbfQbzfT3nZHOYxXAsondwemMfSMkVFUYL5QykscV8vPW5gIOdd8Aql1NG1DelA0F/1EO9SwOgf0J9u7vcA5m+nziEBfqarc9g9NbwUo0n2glWiwsBa7qbcKKWY4bfcJ6CeQkKRpbbYwqzY6WAsSl/AYmzVgzRsH8BemmrQMzygnqHdgx6g+P365U9G7wyy0B/zgcM+O7CYNTVPSAbtwM/5af8lH9UzNE73Ywh/j9uNnzLO56etM0Nn/2Bq5z0hFzacaukjbZ3H1F6dLbCVHJo7RvbtjYd5xNHWKZVH5zUv7NouVFnszr3oX83vUZqda6uL42Pa6h9Y9ZRFN70m87ozgL/qr+O3CzvTjKh/3J0s4UzDR/pr4eC88KtLfWb0HKzuDWJTl/0neFccpINPP1lIjhpu/Wopm+b1Z1DizqdaTRofbBZnNAra+tZjZO2cGqcNP0NcyDRF27rzbZN/ytriGeB9omz4+2g5+VGElc1dlPIBAzeuXPLmX7qexXvedlhvNgld9Y3buvSdLGWdT7NDq5XnfpMP2g+tl5rWka6YOnHBlgtIyRGjrHUvqcGppdjK1mgUStP62eerimdqgZllA28rOj52UmyPmMBTb/ehXzoh+pQcMJYzhu+/gQae3SueZ9VhYzp5Y4p2kD95uLpZwjCJpExq1MD24bPHqJErqM6YdyDGYRnI6gG5HHU5LpmdSz2lMo+T765qlSwT0El1tXVcV/Jd5eaMN4Pwuv60QY6RPA9SxUm2YPmcWr8+beSbPGl5VItff8rfztfqZV0JSoiKrAURQ4LSLzoQL4L9ce+OEuWPFDyqFjXLy/qhqhWNR5fNzK0rogoingH+je/AyiNE1ZiSCT2Obv/AJm6TUk='
favicon_base64_data = zlib_decompress(b64decode(compressed_favicon_base64_data)).decode('utf-8')

# Setup error handlers
def show_error_page(error_code: int, custom_error_name: str = None) -> Tuple[render_template, int]:
    if not custom_error_name:
        error_name = HTTPStatus(error_code).phrase
        custom_error_name = error_name

    return render_template('httpweberrors.html', error_code=error_code, error_name=custom_error_name, favicon_base64_data=favicon_base64_data), error_code


@app.errorhandler(404)
@cache.cached(timeout=1, make_cache_key=CacheTools.gen_cache_key)
def page_not_found(error: Exception) -> Tuple[render_template, int]: return show_error_page(error_code=404)


@app.errorhandler(429)
@cache.cached(timeout=1, make_cache_key=CacheTools.gen_cache_key)
def ratelimit_exceeded(error: Exception) -> Tuple[render_template, int]: return show_error_page(error_code=429)


@app.errorhandler(500)
@cache.cached(timeout=1, make_cache_key=CacheTools.gen_cache_key)
def internal_server_error(error: Exception) -> Tuple[render_template, int]: return show_error_page(error_code=500)


@app.errorhandler(503)
@cache.cached(timeout=1, make_cache_key=CacheTools.gen_cache_key)
def service_unavailable(error: Exception) -> Tuple[render_template, int]: return show_error_page(error_code=503)


# Setup main routes
@app.route('/', methods=['GET'])
@limiter.limit(LimiterTools.gen_ratelimit_message(per_min=120))
@cache.cached(timeout=86400, make_cache_key=CacheTools.gen_cache_key)
def initial_page() -> Tuple[render_template, int]:
    return render_template('index.html', favicon_base64_data=favicon_base64_data), 200


@app.route('/docs', methods=['GET'])
@limiter.limit(LimiterTools.gen_ratelimit_message(per_min=120))
@cache.cached(timeout=86400, make_cache_key=CacheTools.gen_cache_key)
def docs_page() -> redirect:
    return redirect('https://everytoolsapi.docs.apiary.io', code=302)


_api__status = APIEndpoints.v2.status
@app.route('/api/status', methods=['GET'])
@limiter.limit(LimiterTools.gen_ratelimit_message(per_sec=2, per_min=120))
@cache.cached(timeout=1, make_cache_key=CacheTools.gen_cache_key)
def status_page() -> Tuple[jsonify, int]:
    generated_data = _api__status(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


# Setup API routes
_useragent_parser = APIEndpoints.v2.useragent_parser
@app.route(f'/api/<query_version>/{_useragent_parser.endpoint_url}', methods=_useragent_parser.allowed_methods)
@limiter.limit(_useragent_parser.ratelimit)
@cache.cached(timeout=_useragent_parser.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __useragent_parser(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _useragent_parser.ready_to_production: return show_error_page(error_code=503)
    generated_data = _useragent_parser.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_url_parser = APIEndpoints.v2.url_parser
@app.route(f'/api/<query_version>/{_url_parser.endpoint_url}', methods=_url_parser.allowed_methods)
@limiter.limit(_url_parser.ratelimit)
@cache.cached(timeout=_url_parser.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __url_parser(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _url_parser.ready_to_production: return show_error_page(error_code=503)
    generated_data = _url_parser.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_seconds_to_hhmmss_format_converter = APIEndpoints.v2.seconds_to_hhmmss_format_converter
@app.route(f'/api/<query_version>/{_seconds_to_hhmmss_format_converter.endpoint_url}', methods=_seconds_to_hhmmss_format_converter.allowed_methods)
@limiter.limit(_seconds_to_hhmmss_format_converter.ratelimit)
@cache.cached(timeout=_seconds_to_hhmmss_format_converter.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __seconds_to_hhmmss_format_converter(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _seconds_to_hhmmss_format_converter.ready_to_production: return show_error_page(error_code=503)
    generated_data = _seconds_to_hhmmss_format_converter.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_email_parser = APIEndpoints.v2.email_parser
@app.route(f'/api/<query_version>/{_email_parser.endpoint_url}', methods=_email_parser.allowed_methods)
@limiter.limit(_email_parser.ratelimit)
@cache.cached(timeout=_email_parser.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __email_parser(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _email_parser.ready_to_production: return show_error_page(error_code=503)
    generated_data = _email_parser.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_advanced_text_counter = APIEndpoints.v2.advanced_text_counter
@app.route(f'/api/<query_version>/{_advanced_text_counter.endpoint_url}', methods=_advanced_text_counter.allowed_methods)
@limiter.limit(_advanced_text_counter.ratelimit)
@cache.cached(timeout=_advanced_text_counter.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __advanced_text_counter(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _advanced_text_counter.ready_to_production: return show_error_page(error_code=503)
    generated_data = _advanced_text_counter.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_text_language_detector = APIEndpoints.v2.text_language_detector
@app.route(f'/api/<query_version>/{_text_language_detector.endpoint_url}', methods=_text_language_detector.allowed_methods)
@limiter.limit(_text_language_detector.ratelimit)
@cache.cached(timeout=_text_language_detector.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __text_language_detector(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _text_language_detector.ready_to_production: return show_error_page(error_code=503)
    generated_data = _text_language_detector.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_text_translator = APIEndpoints.v2.text_translator
@app.route(f'/api/<query_version>/{_text_translator.endpoint_url}', methods=_text_translator.allowed_methods)
@limiter.limit(_text_translator.ratelimit)
@cache.cached(timeout=_text_translator.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __text_translator(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _text_translator.ready_to_production: return show_error_page(error_code=503)
    generated_data = _text_translator.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_my_ip = APIEndpoints.v2.my_ip
@app.route(f'/api/<query_version>/{_my_ip.endpoint_url}', methods=_my_ip.allowed_methods)
@limiter.limit(_my_ip.ratelimit)
@cache.cached(timeout=_my_ip.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __my_ip(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _my_ip.ready_to_production: return show_error_page(error_code=503)
    generated_data = _my_ip.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_get_latest_ffmpeg_download_url = APIEndpoints.v2.get_latest_ffmpeg_download_url
@app.route(f'/api/<query_version>/{_get_latest_ffmpeg_download_url.endpoint_url}', methods=_get_latest_ffmpeg_download_url.allowed_methods)
@limiter.limit(_get_latest_ffmpeg_download_url.ratelimit)
@cache.cached(timeout=_get_latest_ffmpeg_download_url.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __get_latest_ffmpeg_download_url(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _get_latest_ffmpeg_download_url.ready_to_production: return show_error_page(error_code=503)
    generated_data = _get_latest_ffmpeg_download_url.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_ffprobe_a_video_url = APIEndpoints.v2.ffprobe_a_video_url
@app.route(f'/api/<query_version>/{_ffprobe_a_video_url.endpoint_url}', methods=_ffprobe_a_video_url.allowed_methods)
@limiter.limit(_ffprobe_a_video_url.ratelimit)
@cache.cached(timeout=_ffprobe_a_video_url.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __ffprobe_a_video_url(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _ffprobe_a_video_url.ready_to_production: return show_error_page(error_code=503)
    generated_data = _ffprobe_a_video_url.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_scrap_google_search_results = APIEndpoints.v2.scrap_google_search_results
@app.route(f'/api/<query_version>/{_scrap_google_search_results.endpoint_url}', methods=_scrap_google_search_results.allowed_methods)
@limiter.limit(_scrap_google_search_results.ratelimit)
@cache.cached(timeout=_scrap_google_search_results.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __scrap_google_search_results(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _scrap_google_search_results.ready_to_production: return show_error_page(error_code=503)
    generated_data = _scrap_google_search_results.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_scrap_instagram_reel_url = APIEndpoints.v2.scrap_instagram_reel_url
@app.route(f'/api/<query_version>/{_scrap_instagram_reel_url.endpoint_url}', methods=_scrap_instagram_reel_url.allowed_methods)
@limiter.limit(_scrap_instagram_reel_url.ratelimit)
@cache.cached(timeout=_scrap_instagram_reel_url.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __scrap_instagram_reels_url(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _scrap_instagram_reel_url.ready_to_production: return show_error_page(error_code=503)
    generated_data = _scrap_instagram_reel_url.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_scrap_tiktok_video_url = APIEndpoints.v2.scrap_tiktok_video_url
@app.route(f'/api/<query_version>/{_scrap_tiktok_video_url.endpoint_url}', methods=_scrap_tiktok_video_url.allowed_methods)
@limiter.limit(_scrap_tiktok_video_url.ratelimit)
@cache.cached(timeout=_scrap_tiktok_video_url.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __scrap_tiktok_video_url(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _scrap_tiktok_video_url.ready_to_production: return show_error_page(error_code=503)
    generated_data = _scrap_tiktok_video_url.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_scrap_youtube_video_url = APIEndpoints.v2.scrap_youtube_video_url
@app.route(f'/api/<query_version>/{_scrap_youtube_video_url.endpoint_url}', methods=_scrap_youtube_video_url.allowed_methods)
@limiter.limit(_scrap_youtube_video_url.ratelimit)
@cache.cached(timeout=_scrap_youtube_video_url.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __scrap_youtube_video_url(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _scrap_youtube_video_url.ready_to_production: return show_error_page(error_code=503)
    generated_data = _scrap_youtube_video_url.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_get_youtube_video_url_from_search = APIEndpoints.v2.get_youtube_video_url_from_search
@app.route(f'/api/<query_version>/{_get_youtube_video_url_from_search.endpoint_url}', methods=_get_youtube_video_url_from_search.allowed_methods)
@limiter.limit(_get_youtube_video_url_from_search.ratelimit)
@cache.cached(timeout=_get_youtube_video_url_from_search.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __get_youtube_video_url_from_search(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _get_youtube_video_url_from_search.ready_to_production: return show_error_page(error_code=503)
    generated_data = _get_youtube_video_url_from_search.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


_scrap_soundcloud_track_url = APIEndpoints.v2.scrap_soundcloud_track_url
@app.route(f'/api/<query_version>/{_scrap_soundcloud_track_url.endpoint_url}', methods=_scrap_soundcloud_track_url.allowed_methods)
@limiter.limit(_scrap_soundcloud_track_url.ratelimit)
@cache.cached(timeout=_scrap_soundcloud_track_url.cache_timeout, make_cache_key=CacheTools.gen_cache_key)
def __scrap_soundcloud_track_url(query_version: str) -> Tuple[jsonify, int]:
    if not APIVersion.is_latest_api_version(query_version): return APIVersion.send_invalid_api_version_response(query_version)
    if not _scrap_soundcloud_track_url.ready_to_production: return show_error_page(error_code=503)
    generated_data = _scrap_soundcloud_track_url.run(db_client, APITools.extract_request_data(request))
    return jsonify(generated_data[0]), generated_data[1]


if __name__ == '__main__':
    # Load the configuration file
    current_path = Path(__file__).parent
    config_path = Path(current_path, 'config.yaml')
    config = Config(**yaml_safe_load(config_path.open('r')))

    # Setting up Flask default configuration
    app.static_folder = Path(current_path, config.flask.staticFolder)
    app.template_folder = Path(current_path, config.flask.templateFolder)

    # Run the web server with the specified configuration
    logger.info(f'Starting web server at {config.flask.host}:{config.flask.port}')
    app.run(debug=debugging_mode, host=config.flask.host, port=config.flask.port, threaded=config.flask.threadedServer)
