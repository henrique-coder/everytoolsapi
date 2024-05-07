from time import perf_counter
from typing import Union
from fake_useragent import UserAgent as FakeUserAgent
from httpx import head, _exceptions as httpx_exceptions


def main(_id: str) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()

    try:
        resp = head(f'https://api.pillowcase.su/api/get/{_id}', headers={'User-Agent': FakeUserAgent().random}, timeout=10)
        resp.raise_for_status()

        if resp.status_code not in (200, 302, 307):
            return None

        generated_data['data'] = f'https://api.pillowcase.su/api/download/{_id}'
    except httpx_exceptions.HTTPError:
        return None

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
