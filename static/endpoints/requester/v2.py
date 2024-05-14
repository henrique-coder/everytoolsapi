from httpx import get, _exceptions as httpx_exceptions
from typing import *

from static.dependencies.functions import APITools, OtherTools
from static.dependencies.exceptions import Exceptions


class Requester:
    @staticmethod
    def ip_address(input_values: Dict[str, Optional[Any]]) -> dict:
        output_dict = APITools.get_default_output_dict()

        # Input parameter validation
        if not input_values['remoteIpAddressHeader'] and not input_values['query']:
            output_dict['errorMessage'] = Exceptions.EMPTY_PARAMETERS_VALUE.message.format('remote_ip_address, ip')
            return output_dict

        if input_values['query']: ip_address = input_values['query']
        else: ip_address = input_values['remoteIpAddressHeader']

        # Main process
        try:
            url = f'http://ip-api.com/json/{ip_address}'
            params = {'lang': 'en', 'fields': 'status,message,continent,continentCode,country,countryCode,region,regionName,city,district,zip,lat,lon,timezone,offset,currency,isp,org,as,asname,reverse,mobile,proxy,hosting,query'}
            headers = {'User-Agent': OtherTools.get_random_user_agent()}
            response = get(url, headers=headers, params=params, follow_redirects=False, timeout=10)
            response.raise_for_status()
            dict_data = dict(response.json())
        except (httpx_exceptions.HTTPStatusError, ValueError):
            output_dict['errorMessage'] = Exceptions.ONLINE_REQUEST_FAILED.message
            return output_dict

        if dict_data['status'] == 'success':
            dict_data = APITools.remove_keys_from_dict(dict_data, ['query', 'status', 'message'])

            for key, value in dict_data.items():
                if isinstance(value, str) and not value.strip(): dict_data[key] = None

            output_dict['success'], output_dict['response'] = True, dict_data
            return output_dict
        else:
            if dict_data['message'] == 'private range': output_dict['errorMessage'] = Exceptions.IPAPI_PRIVATE_RANGE.message
            elif dict_data['message'] == 'reserved range': output_dict['errorMessage'] = Exceptions.IPAPI_RESERVED_RANGE.message
            elif dict_data['message'] == 'invalid query': output_dict['errorMessage'] = Exceptions.INVALID_PUBLIC_IP_ADDRESS.message
            else: output_dict['errorMessage'] = Exceptions.ONLINE_REQUEST_FAILED.message
            return output_dict
