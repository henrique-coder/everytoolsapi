from typing import Union
from httpx import get, _exceptions as httpx_exceptions
from bs4 import BeautifulSoup
from time import perf_counter


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
}

main_promotion_websites = {
    'boletando.com': 'https://boletando.com/?s={}&asp_active=1&p_asid=1',
}


def main(_name: str) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = {'data': {'active_promotions': dict(), 'scraped_websites': list()}}

    for website, url in main_promotion_websites.items():
        try:
            resp = get(url.format(_name), headers=headers, timeout=5)
            resp.raise_for_status()
        except httpx_exceptions.HTTPError:
            continue

        generated_data['data']['scraped_websites'].append(website)

        soup = BeautifulSoup(resp.text, 'html.parser')

        if website == 'boletando.com':
            for item in soup.find_all('div', class_='grid_desc_and_btn'):
                product_name = item.find('h3').text.strip()
                if product_name.lower().startswith('[ encerrada ]') or not item.find('span', class_='rh_regular_price'):
                    continue

                generated_data['data']['active_promotions'][product_name] = {
                    'url': item.find('a', class_='re_track_btn')['href'],
                }
        else:
            return None

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
