# Built-in modules
from logging import config as logging_config, getLogger


# Setup logging configuration
logging_config_data = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s (%(module)s): %(message)s',
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
logging_config.dictConfig(logging_config_data)
logger = getLogger(__name__)

# Log initialization
logger.info('Flask application and logger successfully initialized')
