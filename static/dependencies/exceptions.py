from typing import *


class Exceptions:
    class INVALID_FLASK_PORT_ENVIRONMENT_VARIABLE:
        message = 'The FLASK_PORT environment variable must be an integer.'

    class USING_LATEST_API_VERSION:
        message = 'This version is the latest version of the API.'

    class USING_OUTDATED_API_VERSION:
        message = 'This version is outdated. Please use the latest version of the API to be able to use our services.'

    class USING_INVALID_API_VERSION:
        message = 'This version does not exist. Please use the latest version of the API to be able to use our services.'

    class EMPTY_PARAMETERS_VALUE:
        message = 'The parameter(s) "{0}" cannot be empty.'

    class INVALID_PARAMETER_VALUE:
        message = 'The parameter "{0}" has an invalid value. The value must be an "{1}".'

    class PARAMETER_MUST_BE_LESS_THAN:
        message = 'The parameter "{0}" must be less than "{1}".'

    class PARAMETER_MUST_BE_GREATER_THAN:
        message = 'The parameter "{0}" must be greater than {1}.'
