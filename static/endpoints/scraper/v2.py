from yt_dlp import YoutubeDL
from re import compile, search, sub
from datetime import datetime
from unicodedata import normalize
from urllib.parse import unquote
from typing import *

from static.dependencies.functions import APITools
from static.dependencies.exceptions import Exceptions


class Scraper:
    @staticmethod
    def youtube_com(input_values: Dict[str, Optional[Any]]) -> dict:
        output_dict = APITools.get_default_output_dict()

        # Input parameter validation
        if not input_values['query']:
            output_dict['errorMessage'] = Exceptions.EMPTY_PARAMETERS_VALUE.message.format('query')
            return output_dict

        # Main process
        blacklisted_media_url_regexes = list()
        blacklisted_media_urls = r'https?://(?!manifest\.googlevideo\.com)\S+'

        for url in blacklisted_media_urls.split():
            blacklisted_media_url_regexes.append(compile(url))

        def is_blacklisted_media_url(query: str) -> bool:
            return not any(regex.match(query) for regex in blacklisted_media_url_regexes)

        def parse_youtube_url(query: str) -> Dict[str, Optional[Union[bool, str]]]:
            """
            Parse YouTube URL to get video and/or playlist ID.
            :param query: YouTube URL.
            :return: Dictionary with success status, URL type, video ID, and playlist ID.
            """

            result = {'success': False, 'urlType': None, 'videoId': None, 'playlistId': None}

            video_regex = r'(?:(?:youtube\.com\/(?:[^\/\n\s?]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]+))'
            playlist_regex = r'(?:list=)([a-zA-Z0-9_-]+)'

            video_match = search(video_regex, query)
            playlist_match = search(playlist_regex, query)
            valid_domain = 'youtube.com' in query or 'youtu.be' in query

            if valid_domain:
                if video_match:
                    result['success'] = True
                    result['urlType'] = 'video'
                    result['videoId'] = video_match.group(1)

                    if playlist_match:
                        result['playlistId'] = playlist_match.group(1)
                elif playlist_match:
                    result['success'] = True
                    result['urlType'] = 'playlist'
                    result['playlistId'] = playlist_match.group(1)

            return result

        def format_string(query: AnyStr) -> str:
            """
            Format string to remove special characters and normalize it.
            :param query: String to be sanitized.
            :return: Sanitized string.
            """

            normalized_string = normalize('NFKD', str(query)).encode('ASCII', 'ignore').decode('utf-8')
            sanitized_string = str(sub(r'\s+', ' ', sub(r'[^a-zA-Z0-9\-_()[\]{}!$#+,. ]', str(), normalized_string)).strip())
            return sanitized_string

        def extract_media_info(data: dict) -> dict:
            # Media information
            media_id = str(data.get('id', str()))
            media_title = str(data.get('title', str()))
            media_formatted_title = format_string(media_title)
            media_description = str(data.get('description', str()))
            media_upload_time = int(datetime.strptime(str(data.get('upload_date', '0')), '%Y%m%d').timestamp())
            media_duration_time = int(data.get('duration', 0))
            media_formatted_duration_time = str('{:02d}:{:02d}:{:02d}'.format(media_duration_time // 3600, (media_duration_time % 3600) // 60, media_duration_time % 60) if media_duration_time < 360000 else '{:d}:{:02d}:{:02d}'.format(media_duration_time // 3600, (media_duration_time % 3600) // 60, media_duration_time % 60))
            media_categories = list(data.get('categories', list()))
            media_tags = list(data.get('tags', list()))
            view_count = int(data.get('view_count', 0))
            like_count = int(data.get('like_count', 0))
            comment_count = int(data.get('comment_count', 0))
            media_is_streaming = bool(data.get('is_live', False))
            media_is_age_restricted = bool(data.get('age_limit', False))

            # URLs
            media_url = f'https://www.youtube.com/watch?v={media_id}'
            media_short_url = f'https://youtu.be/{media_id}'
            media_embed_url = f'https://www.youtube.com/embed/{media_id}'

            # Channel information
            channel_id = data.get('channel_id', str())
            channel_url = f'https://www.youtube.com/channel/{channel_id}' if channel_id else str()
            channel_name = str(data.get('uploader', str()))
            formatted_channel_name = format_string(channel_name)

            output_data = {'mediaId': media_id, 'mediaTitle': media_title, 'formattedMediaTitle': media_formatted_title, 'mediaDescription': media_description, 'mediaUploadTime': media_upload_time, 'mediaDurationTime': media_duration_time, 'formattedMediaDurationTime': media_formatted_duration_time, 'mediaCategories': media_categories, 'mediaTags': media_tags, 'viewCount': view_count, 'likeCount': like_count, 'commentCount': comment_count, 'mediaIsStreaming': media_is_streaming, 'mediaIsAgeRestricted': media_is_age_restricted, 'mediaUrl': media_url, 'mediaShortUrl': media_short_url, 'mediaEmbedUrl': media_embed_url, 'channelId': channel_id, 'channelUrl': channel_url, 'channelName': channel_name, 'formattedChannelName': formatted_channel_name}
            return output_data

        def is_video_data(data: Any) -> bool:
            return data['vcodec'] != 'none' and not data.get('abr')

        def is_audio_data(data: Any) -> bool:
            return data.get('acodec', str()) != 'none'

        def extract_media_subtitles(data: dict) -> list:
            subtitles_data = data.get('subtitles', dict())
            output_subtitle_info = list()

            for lang, subs in subtitles_data.items():
                for sub_info in subs:
                    subtitle_data = {'url': str(unquote(sub_info.get('url', str()))), 'lang': str(lang), 'ext': str(sub_info.get('ext', str()))}
                    output_subtitle_info.append(subtitle_data)

            return output_subtitle_info

        response = parse_youtube_url(input_values['query'])
        if not response.get('success', False):
            output_dict['errorMessage'] = Exceptions.INVALID_YOUTUBE_URL.message
            return output_dict
        elif response.get('urlType') != 'video':
            output_dict['errorMessage'] = Exceptions.NOT_VIDEO_YOUTUBE_URL.message
            return output_dict

        # Start the YouTube extraction process
        url = f'https://www.youtube.com/watch?v={response["videoId"]}'

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'geo_bypass': True,
        }
        yt = YoutubeDL(ydl_opts)

        try:
            extracted_data = yt.sanitize_info(yt.extract_info(url, download=False), remove_private_keys=True)
            info = {'info': extract_media_info(extracted_data), 'media': {'video': list(), 'audio': list(), 'subtitles': list()}}
        except BaseException as e:
            output_dict['errorMessage'] = Exceptions.YOUTUBE_MEDIA_URL_INACCESSIBLE.message
            return output_dict

        media_data = info['media']

        for format_data in extracted_data['formats']:
            # Add video data
            if is_video_data(format_data):
                url = str(unquote(format_data.get('url', str())))

                if not is_blacklisted_media_url(url):
                    size = format_data.get('filesize', None)

                    if size:
                        data = {
                            'url': url,
                            'quality': int(format_data.get('height', 0)),
                            'codec': str(format_data.get('vcodec', str())).split('.')[0],
                            'framerate': int(format_data.get('fps', 0)),
                            'bitrate': int(format_data.get('tbr', 0)),
                        }
                        media_data['video'].append(data)
            # Add audio data
            elif is_audio_data(format_data):
                url = str(unquote(format_data.get('url', str())))

                if not is_blacklisted_media_url(url):
                    size = format_data.get('filesize', None)
                    bitrate = format_data.get('abr', None)

                    if size and bitrate:
                        codec = str(format_data.get('acodec', str())).split('.')[0]
                        samplerate = int(format_data.get('asr', 0))

                        data = {
                            'url': url,
                            'codec': codec,
                            'bitrate': int(bitrate),
                            'samplerate': samplerate,
                            'size': int(size),
                        }
                        media_data['audio'].append(data)

        # Add subtitle data
        media_data['subtitles'] = extract_media_subtitles(extracted_data)

        # Add media data to the output dictionary
        output_dict['response'] = media_data
        return output_dict
