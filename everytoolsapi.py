import flask
from flask_caching import Cache
from flask_limiter import util as flask_limiter_utils, Limiter
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from flask_compress import Compress
from logging.config import dictConfig
from json import load as load_json
from pathlib import Path
from typing import *

from static.data.version import APIVersion
from static.data.functions import APITools, CacheTools


# Get the latest API version
latest_api_version = APIVersion().get_latest_version()

# Configuration class
class Config:
    def __init__(self, **entries: Dict[str, Any]) -> None:
        for key, value in entries.items():
            if isinstance(value, dict):
                value = Config(**value)

            self.__dict__[key] = value


# Setup Flask application and context
app = flask.Flask(__name__)
app.app_context().push()

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

# Setup Flask cache
app.config['CACHE_TYPE'] = 'simple'
cache = Cache(app)

# Setup Talisman for security headers (with custom options), CSRF protection and better compression
limiter = Limiter(flask_limiter_utils.get_remote_address, app=app)
talisman = Talisman(app, content_security_policy={'default-src': ['\'self\'', 'https://cdnjs.cloudflare.com'], 'style-src': ['\'self\'', '\'unsafe-inline\'', 'https://cdnjs.cloudflare.com'], 'script-src': ['\'self\'', 'https://cdnjs.cloudflare.com']})
csrf = CSRFProtect(app)
compression = Compress(app)

# Setup Flask routes
@app.route('/', methods=['GET'])
@cache.cached(timeout=3600, make_cache_key=CacheTools.get_cache_key)
def initial_page() -> Any:
    return flask.render_template('index.html')


@app.route('/api/<query_version>/parser/user-agent/', methods=['GET'])
@cache.cached(timeout=300, make_cache_key=CacheTools.get_cache_key)
def parser_user_agent(query_version: str) -> Any:
    APITools.check_main_request(flask.request.remote_addr, (1, 30, 400, 1000), query_version)
    return flask.jsonify({'userAgent': flask.request.headers.get('User-Agent')})


if __name__ == '__main__':
    # Load the configuration file
    current_path = Path(__file__).parent
    config_path = Path(current_path, 'config.json')
    config = Config(**load_json(config_path.open('r')))

    # Setting up Flask default configuration
    app.static_folder = Path(current_path, config.flask.staticFolder)
    app.template_folder = Path(current_path, config.flask.templateFolder)

    # Run the web server with the specified configuration
    app.run(host=config.flask.host, port=config.flask.port, threaded=config.flask.threadedServer, load_dotenv=config.flask.loadEnvironmentVariables, debug=config.flask.debugMode)
