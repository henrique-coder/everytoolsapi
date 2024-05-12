from httpx import get, _exceptions as httpx_exceptions
from user_agents import parse as UserAgentParser
from typing import *

from static.dependencies.functions import APITools
from static.dependencies.exceptions import Exceptions


output_dict = {'success': False, 'errorMessage': str(), 'response': dict()}


class Requester:
    @staticmethod
    def user_agent(headers: Any, value: Any) -> dict:
        # Input parameter validation
        headers, value = APITools.set_none_if_empty(headers), APITools.set_none_if_empty(value)

        if not value and not headers:
            output_dict['errorMessage'] = Exceptions.EMPTY_PARAMETERS_VALUE.message.format('headers, value')
            return output_dict

        if value: ua_string = value
        else:
            try: headers = dict(headers)
            except ValueError:
                output_dict['errorMessage'] = Exceptions.INVALID_REQUEST_HEADERS.message
                return output_dict

            if 'User-Agent' in headers: ua_string = headers['User-Agent']
            else:
                output_dict['errorMessage'] = Exceptions.USER_AGENT_HEADER_NOT_FOUND.message
                return output_dict

        # Main process
        user_agent = UserAgentParser(ua_string)
        output_data = {
            'ua_string': user_agent.ua_string,
            'os': {'family': user_agent.os.family, 'version': user_agent.os.version, 'version_string': user_agent.os.version_string},
            'browser': {'family': user_agent.browser.family, 'version': user_agent.browser.version, 'version_string': user_agent.browser.version_string},
            'device': {'family': user_agent.device.family, 'brand': user_agent.device.brand, 'model': user_agent.device.model}
        }

        for key, value in output_data.items():
            if isinstance(value, str) and not value.strip(): output_data[key] = None

        output_dict['success'], output_dict['response'] = True, output_data
        return output_dict

    @staticmethod
    def ip_address(remote_ip_address: Any, ip: Any) -> dict:
        # Input parameter validation
        remote_ip_address, ip = APITools.set_none_if_empty(remote_ip_address), APITools.set_none_if_empty(ip)

        if not ip and not remote_ip_address:
            output_dict['errorMessage'] = Exceptions.EMPTY_PARAMETERS_VALUE.message.format('remote_ip_address, ip')
            return output_dict

        if ip: ip_address = ip
        else: ip_address = remote_ip_address

        # Main process
        try:
            url = f'http://ip-api.com/json/{ip_address}'
            params = {'lang': 'en', 'fields': 'status,message,continent,continentCode,country,countryCode,region,regionName,city,district,zip,lat,lon,timezone,offset,currency,isp,org,as,asname,reverse,mobile,proxy,hosting,query'}
            response = get(url, params=params, follow_redirects=False, timeout=10)
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
            if dict_data['message'] == 'private range': output_dict['errorMessage'] = Exceptions.IPAPI_PRIVATE_RANGE.message.format(ip_address)
            elif dict_data['message'] == 'reserved range': output_dict['errorMessage'] = Exceptions.IPAPI_RESERVED_RANGE.message.format(ip_address)
            elif dict_data['message'] == 'invalid query': output_dict['errorMessage'] = Exceptions.INVALID_PUBLIC_IP_ADDRESS.message.format(ip_address)
            else: output_dict['errorMessage'] = Exceptions.ONLINE_REQUEST_FAILED.message
            return output_dict
