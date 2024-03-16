from typing import Union
from httpx import head, _exceptions as httpx_exceptions


headers = {
    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
}


def main(_id: str) -> Union[str, None]:
    try:
        resp = head(f'https://api.pillowcase.su/api/get/{_id}', headers=headers, timeout=5)

        if resp.status_code not in (200, 302, 307):
            return None
    except httpx_exceptions.HTTPError:
        return None

    return f'https://api.pillowcase.su/api/download/{_id}'
