from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from httpx import get, _exceptions as httpx_exceptions
from bs4 import BeautifulSoup
from urllib.parse import unquote
from time import perf_counter, sleep
from typing import Union


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
}

main_promotion_websites = {
    'boletando.com': 'https://boletando.com/?s={}&asp_active=1&p_asid=1',
}

selenium_options = Options()
selenium_options.headless = True


def main(_name: str) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = {'data': {'active_promotions': dict(), 'scraped_websites': list()}}

    for website, url in main_promotion_websites.items():
        def get_html_source_by_get_request(_url: str) -> Union[str, None]:
            try:
                resp = get(_url, headers=headers, timeout=5)
                resp.raise_for_status()
                return resp.text
            except httpx_exceptions.HTTPError:
                return None

        def get_html_source_by_selenium(_url: str, sleep_time: int) -> Union[str, None]:
            try:
                selenium_driver = webdriver.Chrome(options=selenium_options)
                selenium_driver.get(_url)
                sleep(sleep_time)
                extracted_html = selenium_driver.page_source
                selenium_driver.quit()
                return extracted_html
            except Exception:
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
