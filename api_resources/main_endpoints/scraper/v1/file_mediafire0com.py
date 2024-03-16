from typing import Union
from httpx import get, _exceptions as httpx_exceptions
from lxml import html


def main(_id: str) -> Union[str, None]:
    url = f'https://www.mediafire.com/file/{_id}'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
    }

    try:
        resp = get(url, headers=headers, timeout=5)
    except httpx_exceptions.HTTPError:
        return None

    try:
        tree = html.fromstring(resp.content)
        data = tree.xpath('//a[@id="downloadButton"]/@href')[0]
        data = str(data[:data.rfind('/')])
    except Exception:
        return None

    return data
