from httpx import get, _exceptions as httpx_exceptions
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from json import loads as json_loads
from re import compile as re_compile
from time import perf_counter
from typing import Union


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
    'Cookie': 'xman_f=82eZ73Yk3kUmArs2cqSaeVhIBpZUqa5s/nFuPNZUbJduW17e9ELWYOdwJD9yZAawfaLD8+Yi69pXnJy2qhqQWnyq5vD3lfKYXc8WGgVIsu4ExnaqS8zejw==;aep_usuc_f=site=usa&c_tp=USD&region=US&b_locale=en_US',
}


def main(_id: str) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()

    url = f'https://www.aliexpress.us/item/{_id}.html'

    try:
        resp = get(url, follow_redirects=True, headers=headers, timeout=5)
        resp.raise_for_status()
    except httpx_exceptions.HTTPError:
        return None

    try:
        soup = BeautifulSoup(resp.content, 'html.parser')
        data = soup.find('script', string=re_compile(r'window.runParams\s*=\s*{')).string.strip().replace('\n', str())
        raw_data = dict(json_loads(data[data.find('{', data.find('{') + 1): data.rfind('}')], strict=True))
    except BaseException:
        return None

    is_debug_mode = False

    # Section: Store Info
    try:
        store_info__id = raw_data['sellerComponent']['storeNum']
        if store_info__id:
            store_info__id = int(store_info__id)
        else:
            store_info__id = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] store_info__id: {e}')
        store_info__id = None

    try:
        store_info__name = raw_data['storeHeaderComponent']['storeHeaderResult']['storeName']
        if store_info__name:
            store_info__name = str(store_info__name)
        else:
            store_info__name = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] store_info__name: {e}')
        store_info__name = None

    try:
        store_info__homepage_url = raw_data['storeHeaderComponent']['storeHeaderResult']['tabList'][0]['url']
        if store_info__homepage_url:
            store_info__homepage_url = str('https:' + urljoin(str(), store_info__homepage_url))
        else:
            store_info__homepage_url = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] store_info__homepage_url: {e}')
        store_info__homepage_url = None

    try:
        store_info__products_url = raw_data['storeHeaderComponent']['storeHeaderResult']['tabList'][1]['url']
        if store_info__products_url:
            store_info__products_url = str('https:' + urljoin(str(), store_info__products_url))
        else:
            store_info__products_url = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] store_info__products_url: {e}')
        store_info__products_url = None

    try:
        store_info__promotions_url = raw_data['storeHeaderComponent']['storeHeaderResult']['tabList'][2]['url']
        if store_info__promotions_url:
            store_info__promotions_url = str('https:' + urljoin(str(), store_info__promotions_url))
        else:
            store_info__promotions_url = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] store_info__promotions_url: {e}')
        store_info__promotions_url = None

    try:
        store_info__best_sellers_url = raw_data['storeHeaderComponent']['storeHeaderResult']['tabList'][3]['url']
        if store_info__best_sellers_url:
            store_info__best_sellers_url = str('https:' + urljoin(str(), store_info__best_sellers_url))
        else:
            store_info__best_sellers_url = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] store_info__best_sellers_url: {e}')
        store_info__best_sellers_url = None

    try:
        store_info__reviews_url = raw_data['storeHeaderComponent']['storeHeaderResult']['tabList'][4]['url']
        if store_info__reviews_url:
            store_info__reviews_url = str('https:' + urljoin(str(), store_info__reviews_url))
        else:
            store_info__reviews_url = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] store_info__reviews_url: {e}')
        store_info__reviews_url = None

    try:
        store_info__logo_url = raw_data['sellerComponent']['storeLogo']
        if store_info__logo_url:
            store_info__logo_url = str(urljoin(str(), store_info__logo_url))
        else:
            store_info__logo_url = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] store_info__logo_url: {e}')
        store_info__logo_url = None

    # Section: Product Info
    try:
        product_info__id = _id
        product_info__url = 'https://www.aliexpress.com/item/{}.html'
        if product_info__id:
            product_info__id = int(product_info__id)
            product_info__url = product_info__url.format(product_info__id)
        else:
            product_info__id = None
            product_info__url = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] product_info__id & product_info__url: {e}')
        product_info__id = None
        product_info__url = None

    try:
        product_info__name = raw_data['productInfoComponent']['subject']
        if product_info__name:
            product_info__name = str(product_info__name)
        else:
            product_info__name = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] product_info__name: {e}')
        product_info__name = None

    try:
        product_info__description_url = raw_data['productDescComponent']['descriptionUrl']
        if product_info__description_url:
            product_info__description_url = str(str() + urljoin(str(), product_info__description_url))
        else:
            product_info__description_url = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] product_info__description_url: {e}')
        product_info__description_url = None

    try:
        product_info__available_stock = json_loads(raw_data['priceComponent']['skuJson'])[0]['skuVal']['availQuantity']
        if product_info__available_stock:
            product_info__available_stock = int(product_info__available_stock)
        else:
            product_info__available_stock = None
    except BaseException:
        if is_debug_mode:
            print(f'[error] product_info__available_stock: {e}')
        product_info__available_stock = None

    # Section: Product Price
    try:
        product_price__currency_code = json_loads(raw_data['priceComponent']['skuJson'])[0]['skuVal']['skuAmount']['currency']
        if product_price__currency_code:
            product_price__currency_code = str(product_price__currency_code)
        else:
            product_price__currency_code = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] product_price__currency_code: {e}')
        product_price__currency_code = None

    try:
        product_price__original_value = json_loads(raw_data['priceComponent']['skuJson'])[0]['skuVal']['skuAmount']['value']
        if product_price__original_value:
            product_price__original_value = round(float(product_price__original_value), 2)
        else:
            product_price__original_value = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] product_price__original_value: {e}')
        product_price__original_value = None

    try:
        product_price__discount_percentage = json_loads(raw_data['priceComponent']['skuJson'])[0]['skuVal']['discount']
        if product_price__discount_percentage:
            product_price__discount_percentage = round(float(product_price__discount_percentage), 2)
        else:
            product_price__discount_percentage = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] product_price__discount_percentage: {e}')
        product_price__discount_percentage = None

    try:
        product_price__final_price = json_loads(raw_data['priceComponent']['skuJson'])[0]['skuVal']['skuActivityAmount']['value']
        if product_price__final_price:
            product_price__final_price = round(float(product_price__final_price), 2)
        else:
            product_price__final_price = None
    except BaseException as e:
        if is_debug_mode:
            print(f'[error] product_price__final_price: {e}')
        product_price__final_price = None

    formatted_data = {
        'store_info': {
            'id': store_info__id,
            'name': store_info__name,
            'homepage_url': store_info__homepage_url,
            'products_url': store_info__products_url,
            'promotions_url': store_info__promotions_url,
            'best_sellers_url': store_info__best_sellers_url,
            'reviews_url': store_info__reviews_url,
            'logo_url': store_info__logo_url,
        },
        'product_info': {
            'id': product_info__id,
            'url': product_info__url,
            'name': product_info__name,
            'description_url': product_info__description_url,
            'available_stock': product_info__available_stock,
        },
        'product_price': {
            'currency_code': product_price__currency_code,
            'original_value': product_price__original_value,
            'discount_percentage': product_price__discount_percentage,
            'final_price': product_price__final_price,
        }
    }

    generated_data['data'] = formatted_data
    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
