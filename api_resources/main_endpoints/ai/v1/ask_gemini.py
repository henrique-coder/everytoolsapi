from typing import Union
from httpx import head, get, post
from base64 import b64encode
from time import perf_counter


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
}

def main(gemini_api_keys: list, prompt: str, image_url: str = None) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()

    prompt = str(prompt).strip()
    if not image_url or not str(image_url).strip(): image_url = None
    max_tokens = 10000

    def detect_mimetype(url: str) -> Union[str, None]:
        try:
            response = head(url, headers=headers, follow_redirects=True, timeout=5)
            response.raise_for_status()

            if response.status_code == 200:
                content_type = response.headers['Content-Type']

                if not content_type or not str(content_type).strip():
                    return None
                else:
                    return content_type.strip().lower()
            else:
                return None
        except BaseException:
            return None

    def get_url_bytes(url: str) -> Union[bytes, None]:
        try:
            response = get(url, headers=headers, follow_redirects=True, timeout=5)
            response.raise_for_status()

            if response.status_code == 200:
                content = response.content

                if content:
                    return content
                else:
                    return None
            else:
                return None
        except BaseException:
            return None

    available_models = {'text_only': 'gemini-pro', 'text_and_image': 'gemini-pro-vision'}

    params = {'key': None}
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
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

    allowed_image_mime_types = ['image/png', 'image/jpeg', 'image/webp', 'image/heic', 'image/heif']
    image_mimetype = None
    has_image = False

    if image_url:
        image_mimetype = detect_mimetype(image_url)

        if image_mimetype in allowed_image_mime_types:
            image_bytes = get_url_bytes(image_url)

            if image_bytes:
                has_image = True
        elif image_url:
            return None

    if has_image:
        used_model = available_models['text_and_image']
        api_url = f'https://generativelanguage.googleapis.com/v1beta/models/{used_model}:generateContent'
        body['contents'][0]['parts'].append({'inline_data': {'mime_type': image_mimetype, 'data': b64encode(image_bytes).decode('utf-8')}})
    else:
        used_model = available_models['text_only']
        api_url = f'https://generativelanguage.googleapis.com/v1beta/models/{used_model}:generateContent'

    try:
        attempt_number = 0
        response = None

        while attempt_number < len(gemini_api_keys):
            params['key'] = gemini_api_keys[attempt_number]
            response = post(api_url, params=params, headers=headers, json=body, timeout=40)

            if response.status_code == 200:
                break
            else:
                attempt_number += 1

        if response.status_code != 200:
            return None

        generated_data['data'] = {'text': response.json()['candidates'][0]['content']['parts'][0]['text'], 'model': used_model, 'max_tokens': max_tokens}
        generated_data['processing_time'] = float(perf_counter() - start_time)
        return generated_data
    except BaseException:
        return None
