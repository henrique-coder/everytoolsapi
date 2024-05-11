from base64 import b64encode
from time import perf_counter
from fake_useragent import UserAgent as FakeUserAgent
from httpx import head, get, post
from langcodes import Language, LanguageTagError
from typing import *


user_agent = FakeUserAgent()


class AI:
    """
    Main artificial intelligence class.
    """

    class Model:
        """
        A class to interact with some AI models using many different ways.
        """

        def __init__(self, model: Union[Literal['gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-3.5-turbo-16k-0613', 'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-instruct', 'gpt-3.5-turbo-0125', 'gpt-4', 'gpt-4-turbo', 'gpt-4-turbo-preview', 'gpt-4-32k', 'gpt-4-32k-0613', 'gpt-4-0613', 'gpt-4-1106-preview', 'gpt-4-0125-preview', 'gpt-4-turbo-2024-04-09', 'claude-3-haiku', 'claude-3-sonnet', 'claude-3-opus', 'pplx-7b-chat', 'pplx-70b-chat'], str], default_chat_language: str = None) -> None:
            """
            Initialize the AI model.
            :param model: The AI model to be used. Allowed models are:
            :param default_chat_language: The default chat language. If you don't want to use a default chat language, leave it empty.
            """

            if '-' in model:
                if model.startswith('-') or model.endswith('-'):
                    raise Exception(f'The model "{model}" is not allowed. The model must not have the “-” character at the beginning or end of the string.')
            else:
                raise Exception(f'The model "{model}" is not allowed. The model must have prefix and suffix separated by "-". Example: "gpt-4-turbo" (prefix: "gpt", suffix: "4-turbo").')

            self.user_agent = user_agent
            self.chat_history: List[Dict[str, str]] = list()
            self.model = model
            self.model_prefix, self.model_suffix = self.model.split('-', 1) if '-' in self.model else self.model

            if not default_chat_language:
                self.default_chat_language = None
            else:
                error_message = f'The language "{default_chat_language}" is not supported. Please use a valid ISO 639-1 code.'

                try:
                    lang_name = Language.get(default_chat_language).display_name('en-us')
                except LanguageTagError:
                    raise Exception(error_message)

                if 'Unknown language' in lang_name:
                    raise Exception(error_message)

                self.default_chat_language = lang_name

        def ask(self, prompt: str, save_to_chat_history: bool = True) -> Dict[str, Union[str, float]]:
            """
            Interact with some AI models using many different ways.
            :param prompt: The prompt to be sent to the AI model.
            :param save_to_chat_history: If the prompt should be saved to the chat history.
            :return: A dictionary with the response and the elapsed time.
            """

            av_ep = {0: 'https://api.discord.rocks/ask', 1: 'https://gpt4.discord.rocks/ask'}

            models = {
                'gpt': {
                    '3.5-turbo': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '3.5-turbo-16k': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '3.5-turbo-16k-0613': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '3.5-turbo-0613': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '3.5-turbo-1106': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '3.5-turbo-instruct': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '3.5-turbo-0125': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '4': {'urls': [av_ep[0], av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '4-turbo': {'urls': [av_ep[0]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '4-turbo-preview': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '4-32k': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '4-32k-0613': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '4-0613': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '4-1106-preview': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '4-0125-preview': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '4-turbo-2024-04-09': {'urls': [av_ep[1]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                },
                'claude': {
                    '3-haiku': {'urls': [av_ep[0]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '3-sonnet': {'urls': [av_ep[0]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '3-opus': {'urls': [av_ep[0]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                },
                'pplx': {
                    '7b-chat': {'urls': [av_ep[0]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                    '70b-chat': {'urls': [av_ep[0]], 'allowChatHist': True, 'textGen': True, 'imageGen': False},
                },
            }

            if self.model_prefix in models:
                if self.model_suffix in models[self.model_prefix]:
                    pass
                else:
                    raise Exception(f'The model suffix "{self.model_suffix}" is not allowed. Allowed model suffixes for the model prefix "{self.model_prefix}" are: {", ".join(models[self.model_prefix])}.')
            else:
                raise Exception(f'The model prefix "{self.model_prefix}" is not allowed. Allowed model prefixes are: {", ".join(models)}.')

            headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': self.user_agent.random}
            json_data = {'messages': self.chat_history, 'model': self.model}

            if self.default_chat_language:
                self.chat_history.append({'role': 'system', 'content': f'The default language of this chat will be {self.default_chat_language}. You must answer all my messages in this chat in that language, without errors or glitches, in a natural way.'})

            if save_to_chat_history:
                self.chat_history.append({'role': 'user', 'content': prompt})

            try:
                base_api_url = models[self.model_prefix][self.model_suffix]['urls'][0]
                response = post(base_api_url, headers=headers, json=json_data, follow_redirects=False, timeout=3600)
                response.raise_for_status()
                output_text_response = str(response.json()['response'])
                if output_text_response in ['Model not found or too long input. Or any other error (xD)', 'Model not found']:
                    raise Exception(output_text_response)
                if save_to_chat_history:
                    self.chat_history.append({'role': 'assistant', 'content': output_text_response})
            except BaseException as e:
                raise Exception(e)

            output_data = {'response': output_text_response,  'model': str(self.model)}

            return output_data


def main(json_data: Optional[list], model: str, prompt: str, image_url: str = None, gemini_api_keys: list = None) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()
    prompt = str(prompt).strip()

    if model not in ['gemini-pro', 'gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-3.5-turbo-16k-0613', 'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-instruct', 'gpt-3.5-turbo-0125', 'gpt-4', 'gpt-4-turbo', 'gpt-4-turbo-preview', 'gpt-4-32k', 'gpt-4-32k-0613', 'gpt-4-0613', 'gpt-4-1106-preview', 'gpt-4-0125-preview', 'gpt-4-turbo-2024-04-09', 'claude-3-haiku', 'claude-3-sonnet', 'claude-3-opus', 'pplx-7b-chat', 'pplx-70b-chat']:
        return None

    if model == 'gemini-pro':
        if not image_url or not str(image_url).strip(): image_url = None
        max_tokens = 10000

        def detect_mimetype(url: str) -> Union[str, None]:
            try:
                response = head(url, headers={'User-Agent': user_agent.random}, follow_redirects=True, timeout=10)
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
                response = get(url, headers={'User-Agent': user_agent.random}, follow_redirects=True, timeout=10)
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
        headers = {'User-Agent': user_agent.random, 'Content-Type': 'application/json', 'Accept': 'application/json'}
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

            generated_data['data'] = {'text': response.json()['candidates'][0]['content']['parts'][0]['text'], 'model': used_model}
            generated_data['processing_time'] = float(perf_counter() - start_time)
            return generated_data
        except BaseException:
            return None
    else:
        generated_data['data'] = dict()

        ai = AI.Model(model=model)

        if json_data:
            ai.chat_history = json_data

        output_data = ai.ask(prompt, True)
        generated_data['data']['text'] = output_data['response']
        generated_data['data']['model'] = output_data['model']
        generated_data['processing_time'] = float(perf_counter() - start_time)

        return generated_data
