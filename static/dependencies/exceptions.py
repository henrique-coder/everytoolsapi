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

    class INVALID_REQUEST_HEADERS:
        message = 'The request headers are invalid. Please check the headers and try again.'

    class USER_AGENT_HEADER_NOT_FOUND:
        message = 'The "User-Agent" header was not found in the request headers.'

    class ONLINE_REQUEST_FAILED:
        message = 'This request failed, please try again or report this error at https://github.com/Henrique-Coder/everytoolsapi/issues.'

    class INVALID_PUBLIC_IP_ADDRESS:
        message = 'The IP address is invalid ({0}). Please enter a valid public IP address.'

    class IPAPI_PRIVATE_RANGE:
        message = 'The IP address is in a private range ({0}). Please enter a public IP address.'

    class IPAPI_RESERVED_RANGE:
        message = 'The IP address is in a reserved range ({0}). Please enter a public IP address.'
