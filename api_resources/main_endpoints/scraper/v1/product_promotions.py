from time import perf_counter
from urllib.parse import unquote
from bs4 import BeautifulSoup
from fake_useragent import UserAgent as FakeUserAgent
from httpx import get, _exceptions as httpx_exceptions
from typing import *


user_agent = FakeUserAgent()


main_promotion_websites = {
    'boletando.com': 'https://boletando.com/?s={}&asp_active=1&p_asid=1',
}


def main(_name: str) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = {'data': {'active_promotions': dict(), 'scraped_websites': list()}}

    for website, url in main_promotion_websites.items():
        def get_html_source_by_get_request(_url: str) -> Union[str, None]:
            try:
                resp = get(_url, headers={'User-Agent': user_agent.random}, timeout=10)
                resp.raise_for_status()
                return resp.text
            except httpx_exceptions.HTTPError:
                return None

        if website == 'boletando.com':
            url = url.format(_name)
            resp_text = get_html_source_by_get_request(url)
            if not resp_text:
                continue

            soup = BeautifulSoup(resp_text, 'html.parser')

            for item in soup.find_all('div', class_='grid_desc_and_btn'):
                product_name = item.find('h3').text.strip()

                if product_name.lower().startswith('[ encerrada ]') or not item.find('span', class_='rh_regular_price'):
                    continue

                generated_data['data']['active_promotions'][product_name] = {'url': unquote(item.find('a', class_='re_track_btn')['href'])}

        generated_data['data']['scraped_websites'].append(website)

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
