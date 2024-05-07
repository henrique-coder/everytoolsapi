from time import perf_counter
from typing import Union
from fake_useragent import UserAgent as FakeUserAgent
from httpx import get, _exceptions as httpx_exceptions


user_agent = FakeUserAgent()


def main(custom_ip: Union[str, None] = None) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = {'data': dict()}

    if not custom_ip or not str(custom_ip).strip():
        return None

    try:
        response = get(f'http://ip-api.com/json/{custom_ip}?lang=en&fields=66813951', headers={'User-Agent': user_agent.random}, timeout=10)
        response.raise_for_status()

        json_response = response.json()

        if json_response['status'] != 'success':
            return None
    except httpx_exceptions.HTTPStatusError:
        return None

    renamed_keys = {
        'asname': 'as_name',
        'city': 'city',
        'continent': 'continent',
        'continentCode': 'continent_code',
        'country': 'country_name',
        'countryCode': 'country_code',
        'currency': 'currency',
        'district': 'district',
        'hosting': 'hosting',
        'isp': 'isp',
        'lat': 'latitude',
        'lon': 'longitude',
        'mobile': 'mobile',
        'offset': 'offset',
        'org': 'organization',
        'proxy': 'proxy',
        'region': 'region_code',
        'regionName': 'region_name',
        'reverse': 'reverse',
        'timezone': 'timezone',
        'zip': 'zip_code'
    }

    for key, value in json_response.items():
        renamed_key = renamed_keys.get(key, key)
        generated_data['data'][renamed_key] = value.strip() if isinstance(value, str) else value

        if isinstance(value, str) and not value.strip():
            generated_data['data'][renamed_key] = None

    generated_data['data'].pop('status', None)
    generated_data['data'].pop('query', None)

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
