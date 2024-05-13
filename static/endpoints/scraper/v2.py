from yt_dlp import YoutubeDL
import yt_dlp
import re
from datetime import datetime
from unicodedata import normalize
import urllib.parse


from typing import *

from static.dependencies.functions import APITools
from static.dependencies.exceptions import Exceptions


class Scraper:
    @staticmethod
    def youtube_com(url: str) -> dict:
        def parse_youtube_url(query: str) -> Dict[str, Optional[Union[bool, str]]]:
            """
            Parse YouTube URL to get video and/or playlist ID.
            :param query: YouTube URL.
            :return: Dictionary with success status, URL type, video ID, and playlist ID.
            """

            result = {'success': False, 'urlType': None, 'videoId': None, 'playlistId': None}

            video_regex = r'(?:(?:youtube\.com\/(?:[^\/\n\s?]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]+))'
            playlist_regex = r'(?:list=)([a-zA-Z0-9_-]+)'

            video_match = re.search(video_regex, query)
            playlist_match = re.search(playlist_regex, query)
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

        output_dict = APITools.get_default_output_dict()

        # Input parameter validation
        if not url:
            output_dict['errorMessage'] = Exceptions.EMPTY_PARAMETERS_VALUE.message.format('url')
            return output_dict

        # Main process
        def format_string(query: AnyStr) -> str:
            """
            Format string to remove special characters and normalize it.
            :param query: String to be sanitized.
            :return: Sanitized string.
            """

            normalized_string = normalize('NFKD', str(query)).encode('ASCII', 'ignore').decode('utf-8')
            sanitized_string = str(re.sub(r'\s+', ' ', re.sub(r'[^a-zA-Z0-9\-_()[\]{}!$#+,. ]', str(), normalized_string)).strip())
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

        response = parse_youtube_url(url)
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
        except BaseException as e:
            output_dict['errorMessage'] = Exceptions.YOUTUBE_MEDIA_URL_INACCESSIBLE.message
            return output_dict

        info = {'info': extract_media_info(extracted_data), 'media': {'video': list(), 'audio': list(), 'subtitles': list()}}
        return info
