from yt_dlp import YoutubeDL, utils as yt_dlp_utils
from urllib.parse import unquote
from unicodedata import normalize
from re import sub as re_sub, compile as re_compile
from datetime import datetime
from time import perf_counter
from typing import Union


# Lists with regular expressions with forbidden URLs
blacklisted_url_regexes = [
    re_compile(r'https?://(?!manifest\.googlevideo\.com)\S+'),
]


def main(_id: str) -> Union[dict, None]:
    start_time = perf_counter()
    generated_data = dict()

    # Function to check if it is a valid URL according to the regex
    def is_blacklisted_url(url: str) -> bool:
        return not any(regex.match(url) for regex in blacklisted_url_regexes)

    # Function to check if it is a valid video URL
    def is_video_url(format_info_data: dict) -> bool:
        return format_info_data['vcodec'] != 'none' and not format_info_data.get('abr')

    # Function to format the title
    def sanitize_string(title: str) -> str:
        normalized_string = normalize('NFKD', title).encode('ASCII', 'ignore').decode('utf-8')
        sanitized_string = re_sub(r'\s+', ' ', re_sub(r'[^a-zA-Z0-9\-_()[\]{}!$#+,. ]', str(), normalized_string).strip())

        return sanitized_string

    # Function to extract general video information
    def extract_video_info(info: dict) -> dict:
        video_id = info.get('id', str())
        channel_id = info.get('channel_id', str())
        channel_url = f'https://www.youtube.com/channel/{channel_id}' if channel_id else None
        formatted_channel_name = sanitize_string(info.get('uploader', str()))
        formatted_title = sanitize_string(info.get('title', str()))
        epoch_upload_date = int(datetime.strptime(str(info.get('upload_date', '0')), '%Y%m%d').timestamp())

        return {
            'id': info.get('id', str()),
            'long_url': f'https://www.youtube.com/watch?v={video_id}',
            'short_url': f'https://youtu.be/{video_id}',
            'title': info.get('title', str()),
            'sanitized_title': formatted_title,
            'likes': info.get('like_count', 0),
            'description': info.get('description', str()),
            'upload_date': epoch_upload_date,
            'duration': info.get('duration', 0),
            'views': info.get('view_count', 0),
            'categories': info.get('categories', list()),
            'tags': info.get('tags', list()),
            'channel_id': channel_id,
            'channel_url': channel_url,
            'channel_name': info.get('uploader', str()),
            'sanitized_channel_name': formatted_channel_name,
            'comments': info.get('comment_count', 0),
            'is_streaming': info.get('is_live', False),
            'is_age_restricted': info.get('age_limit', 0) > 0,
        }

    # Function to extract information about subtitles
    def extract_subtitles(info: dict) -> list:
        subtitles = info.get('subtitles', {})
        subtitle_info = list()

        for lang, subs in subtitles.items():
            for sub_info in subs:
                url = unquote(sub_info.get('url', str()))
                subtitle_data = {
                    'url': url,
                    'lang': lang,
                    'ext': sub_info.get('ext', str()),
                }
                subtitle_info.append(subtitle_data)

        return subtitle_info

    # Main function to get video information
    def get_youtube_video_data(video_url) -> Union[dict, None]:
        yt = YoutubeDL(
            {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'geo_bypass': True,
            }
        )

        yt_dlp_utils.std_headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'

        try:
            info = yt.sanitize_info(yt.extract_info(video_url, download=False), remove_private_keys=True)
            data = {'info': extract_video_info(info), 'media': {'video': list(), 'audio': list(), 'subtitles': list()}}
        except Exception:
            return None

        # Adding details about videos, audios, and subtitles in the 'media' key
        media_data = data['media']
        for format_info in info['formats']:
            if is_video_url(format_info):
                _url = str(format_info['url'])
                _quality = int(format_info.get('height', 0))
                _codec = str(format_info['vcodec'])
                _framerate = int(format_info.get('fps', 0))
                _bitrate = int(format_info.get('tbr', 0))

                if not is_blacklisted_url(_url):
                    quality_key = f'{_quality}p' if _quality else None
                    size = int(format_info.get('filesize', 0))

                    # Adding information about videos only if size is not 0
                    if size != 0:
                        media_data['video'].append({
                            'url': unquote(_url),
                            'codec': _codec,
                            'framerate': _framerate,
                            'bitrate': _bitrate,
                            'size': size,
                            'quality': quality_key,
                        })

            if 'acodec' in format_info and format_info['acodec'] != 'none':
                audio_data = {
                    'url': unquote(format_info['url']),
                    'codec': format_info['acodec'],
                    'bitrate': int(format_info.get('abr', 0)),
                    'sample_rate': int(format_info.get('asr', 0)),
                }
                # Adding information about audio only if bitrate is not 0
                if audio_data['bitrate'] != 0:
                    audio_data['size'] = int(format_info.get('filesize', 0))
                    media_data['audio'].append(audio_data)

        # Adding information about subtitles
        subtitle_info = extract_subtitles(info)
        media_data['subtitles'] = subtitle_info

        generated_data['processing_time'] = float(perf_counter() - start_time)
        generated_data['data'] = data

        return generated_data

    return get_youtube_video_data(f'https://www.youtube.com/watch?v={_id}')
