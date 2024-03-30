from typing import Union
from httpx import get, post
from mimetypes import guess_type
from base64 import b64encode
from time import perf_counter


def main(gemini_api_keys: list, prompt: str, image_url: str = None, max_tokens: Union[int, str] = 300) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()

    prompt = prompt.strip() if prompt else None
    image_url = image_url.strip() if image_url else None
    max_tokens = int(max_tokens) if max_tokens else 300

    def detect_mimetype(url: str) -> Union[str, None]:
        try:
            mimetype = guess_type(url)[0]
            return mimetype
        except BaseException:
            return None

    def check_url_content(url: str) -> Union[bytes, None]:
        try:
            response = get(url, follow_redirects=True, timeout=5)
            response.raise_for_status()

            if response.status_code == 200:
                return response.content
            else:
                return None
        except BaseException:
            return None

    available_models = {
        'text_only': 'gemini-pro',
        'text_and_image': 'gemini-pro-vision'
    }

    params = {
        'key': None
    }
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
    }
    body = {
        'contents': [
            {
                'parts': [
                    {
                        'text': prompt
                    },
                ]
            }
        ],
        'generationConfig': {
            'maxOutputTokens': max_tokens,
        }
    }

    image_content = None
    image_mime_type = None

    if image_url:
        image_content = check_url_content(image_url)
    if image_content:
        image_mime_type = detect_mimetype(image_url)

    if image_mime_type:
        model = available_models['text_and_image']
        api_url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
        body['contents'][0]['parts'].append({'inline_data': {'mime_type': image_mime_type, 'data': b64encode(image_content).decode('utf-8')}})
    else:
        model = available_models['text_only']
        api_url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'

    try:
        attempt_number = 0
        response = None

        while attempt_number < len(gemini_api_keys):
            params['key'] = gemini_api_keys[attempt_number]
            response = post(api_url, params=params, headers=headers, json=body, timeout=30)

            if response.status_code == 200:
                break
            else:
                attempt_number += 1

        if response.status_code != 200:
            return None

        generated_data['data'] = {'text': response.json()['candidates'][0]['content']['parts'][0]['text'], 'model': model, 'max_tokens': max_tokens}
        generated_data['processing_time'] = float(perf_counter() - start_time)
        return generated_data
    except BaseException:
        return None
