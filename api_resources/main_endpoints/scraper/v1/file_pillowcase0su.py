from typing import Union
from httpx import head, _exceptions as httpx_exceptions
from time import perf_counter


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
}


def main(_id: str) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()

    try:
        resp = head(f'https://api.pillowcase.su/api/get/{_id}', headers=headers, timeout=5)
        resp.raise_for_status()

        if resp.status_code not in (200, 302, 307):
            return None

        generated_data['url'] = f'https://api.pillowcase.su/api/download/{_id}'
    except httpx_exceptions.HTTPError:
        return None

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
