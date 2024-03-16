from typing import Union
from httpx import get, _exceptions as httpx_exceptions
from lxml import html


def main(_id: str) -> Union[str, None]:
    url = f'https://drive.google.com/uc?export=download&id={_id}'

    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    }

    try:
        resp = get(url, headers=headers, timeout=5)
    except httpx_exceptions.HTTPError:
        return None

    try:
        tree = html.fromstring(resp.content)
        data = tree.xpath('//form[@id="download-form"]/@action')[0]
    except Exception:
        data = url

    return data
