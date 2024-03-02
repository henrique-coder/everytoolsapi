from typing import Union
from httpx import get, _exceptions as httpx_exceptions
from bs4 import BeautifulSoup


def main(_id: str) -> Union[str, None]:
    url = f'https://gofile.io/d/{_id}'

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    }

    try:
        resp = get(url, headers=headers, timeout=5)
    except httpx_exceptions.HTTPError:
        return None

    try:
        soup = BeautifulSoup(resp.content, 'html.parser')

    except Exception:
        return None
