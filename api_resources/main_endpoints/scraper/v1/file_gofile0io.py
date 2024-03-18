from typing import Union
from httpx import get, _exceptions as httpx_exceptions
from lxml import html
from time import perf_counter


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
}


def main(_id: str) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()

    url = f'https://gofile.io/d/{_id}'

    try:
        resp = get(url, headers=headers, timeout=5)
    except httpx_exceptions.HTTPError:
        return None

    try:
        tree = html.fromstring(resp.content)
        generated_data['url'] = None
    except Exception:
        return None

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
