from time import perf_counter
from uuid import uuid4
from fake_useragent import UserAgent as FakeUserAgent
from httpx import head, _exceptions as httpx_exceptions
from typing import *


user_agent = FakeUserAgent()


def main(_id: str) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()

    url = f'https://drive.usercontent.google.com/download?id={_id}&confirm=t&uuid={uuid4()}'

    try:
        resp = head(url, headers={'User-Agent': user_agent.random}, timeout=10)
        resp.raise_for_status()
    except httpx_exceptions.HTTPError:
        return None

    generated_data['data'] = url
    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
