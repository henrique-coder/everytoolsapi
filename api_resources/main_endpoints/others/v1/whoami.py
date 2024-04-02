from typing import Union
from time import perf_counter


def main(headers_data: Union[dict, None]) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = {'data': dict()}

    if not headers_data or 'environ' not in headers_data:
        return None

    environ = headers_data['environ']

    generated_data['data']['ipv4'] = environ.get('REMOTE_ADDR')
    generated_data['data']['ipv6'] = environ.get('HTTP_X_FORWARDED_FOR')
    generated_data['data']['user_agent'] = environ.get('HTTP_USER_AGENT')

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
