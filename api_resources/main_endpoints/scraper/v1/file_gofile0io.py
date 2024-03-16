from typing import Union
from httpx import get, _exceptions as httpx_exceptions
from lxml import html


def main(_id: str) -> Union[str, None]:
    url = f'https://gofile.io/d/{_id}'

    headers = {
        # 'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
    }

    try:
        resp = get(url, headers=headers, timeout=5)
    except httpx_exceptions.HTTPError:
        return None

    try:
        tree = html.fromstring(resp.text)
    except Exception:
        return None


if __name__ == '__main__':
    print(main('mQy16C'))
