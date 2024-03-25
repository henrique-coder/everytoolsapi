from httpx import get, _exceptions as httpx_exceptions
from lxml import html
from time import perf_counter
from typing import Union


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
}


def main(_id: str) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()

    url = f'https://www.mediafire.com/file/{_id}'

    try:
        resp = get(url, headers=headers, timeout=5)
        resp.raise_for_status()
    except httpx_exceptions.HTTPError:
        return None

    try:
        tree = html.fromstring(resp.content)
        data = tree.xpath('//a[@id="downloadButton"]/@href')[0]
        generated_data['data'] = str(data[:data.rfind('/')])
    except Exception:
        return None

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
