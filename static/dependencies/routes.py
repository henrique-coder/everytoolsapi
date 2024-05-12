import flask
from static.dependencies.version import LatestAPIVersion
from static.dependencies.functions import IPRequestLimits, RateLimitFunctions
from typing import *


app = flask.current_app
latest_api_version = LatestAPIVersion().version
