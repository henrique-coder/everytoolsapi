from datetime import datetime
from re import sub as re_sub
from time import perf_counter
from typing import Union
from urllib.parse import unquote
from httpx import head
from unicodedata import normalize
from youtube_dl import YoutubeDL


def main(url: str) -> Union[dict, None]:
    def sanitize_string(string: str) -> str:
        normalized_string = normalize('NFKD', string).encode('ASCII', 'ignore').decode('utf-8')
        sanitized_string = re_sub(r'\s+', ' ', re_sub(r'[^a-zA-Z0-9\-_()[\]{}!$#+,. ]', str(), normalized_string).strip())

        return sanitized_string

    start_time = perf_counter()
    generated_data = {'data': {'info': dict(), 'media': dict()}, 'processing_time': 0.0}

    try:
        ydl_opts = {
            'extractors': ['soundcloud'],
            'format': 'bestaudio/best',
            'quiet': True,
            'force_generic_extractor': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        epoch_upload_date = int(datetime.strptime(str(info.get('upload_date', '0')), '%Y%m%d').timestamp())

        generated_data['data']['info']['title'] = str(info.get('title', str()))
        generated_data['data']['info']['sanitized_title'] = sanitize_string(info.get('title', str()))
        generated_data['data']['info']['long_url'] = unquote(str(info.get('webpage_url', str())))
        generated_data['data']['info']['url'] = unquote(str(info.get('webpage_url', str())))
        generated_data['data']['info']['thumbnail_url'] = unquote(str(info.get('thumbnail', str())))
        generated_data['data']['info']['description'] = str(info.get('description', str()))
        generated_data['data']['info']['artist_name'] = str(info.get('uploader', str()))
        generated_data['data']['info']['sanitized_artist_name'] = sanitize_string(info.get('uploader', str()))
        generated_data['data']['info']['artist_id'] = int(info.get('uploader_id', int()))
        generated_data['data']['info']['artist_url'] = unquote(str(info.get('uploader_url', str())))
        generated_data['data']['info']['view_count'] = int(info.get('view_count', int()))
        generated_data['data']['info']['like_count'] = int(info.get('like_count', int()))
        generated_data['data']['info']['comment_count'] = int(info.get('comment_count', int()))
        generated_data['data']['info']['uploaded_at'] = epoch_upload_date
        generated_data['data']['info']['duration'] = int(info.get('duration', 0))

        generated_data['data']['media']['audio'] = list()
        url = unquote(str(info.get('url', str())))

        generated_data['data']['media']['audio'].append({
            'url': url,
            'codec': str(info.get('format_id', str())),
            'bitrate': int(info.get('abr', 0)),
            'filename': str(generated_data['data']['info']['title'] + '.' + str(info.get('ext', str()))),
            'size': int(head(url, follow_redirects=False, timeout=5).headers.get('Content-Length', 0)),
        })
    except BaseException as e:
        print(f'Error: {e}')
        return None

    generated_data['processing_time'] = float(perf_counter() - start_time)

    return generated_data
