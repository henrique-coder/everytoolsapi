from time import perf_counter
from fake_useragent import UserAgent as FakeUserAgent
from httpx import get, _exceptions as httpx_exceptions
from lxml import html
from typing import *


user_agent = FakeUserAgent()


def main(_id: str) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()

    url = f'https://www.mediafire.com/file/{_id}'

    try:
        resp = get(url, headers={'User-Agent': user_agent.chrome}, timeout=10)
        resp.raise_for_status()
    except httpx_exceptions.HTTPError:
        return None

    try:
        tree = html.fromstring(resp.content)
        data = tree.xpath('//a[@id="downloadButton"]/@href')[0]
        generated_data['data'] = str(data[:data.rfind('/')])
        if generated_data['data'] == r'//www.mediafire.com/file':
            return None
    except BaseException:
        return None

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
