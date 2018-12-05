import argparse
from urllib.parse import parse_qs, urlparse

import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow, argparser
from oauth2client.file import Storage

from Features.AbstractFeature import AbstractFeature


class Youtubable(AbstractFeature):
    @staticmethod
    def description():
        return 'silently adds youtube URLs to a historical playlist.  show playlist with: "!youtube"'

    def __init__(self, client_secret_filename='youtube-oauth2.json', oauth_storage_filename='client_secret.json'):
        self.playlist_id = None  # bot.json_data['optional']['youtube']['playlist']
        self.oauth_storage_filename = oauth_storage_filename
        self.client_secret_filename = client_secret_filename

    def message_filter(self, bot, source, target, message, highlighted):
        self.playlist_id = self.playlist_id or bot.json_data['optional']['youtube']['playlist']

        if "youtu.be/" in message or "youtube.com/watch" in message:
            # grab the URL word
            for word in message.split(' '):
                if "youtu.be" or "youtube.com/watch" in word:
                    # add URL to playlist
                    video_id = self.extract_video_id(word)
                    if video_id:
                        self._add_video_to_playlist(video_id)

        if (message.startswith("youtube") and highlighted) or message.startswith("!youtube"):
            # spit out the URL of the playlist[s]
            bot.message(source, f'https://www.youtube.com/playlist?list={self.playlist_id}')
            return True
        return False

    @staticmethod
    def extract_video_id(word):
        query = urlparse(word)
        if query.hostname == 'youtu.be':
            return query.path[1:]
        if query.hostname in ('www.youtube.com', 'youtube.com'):
            if query.path == '/watch':
                p = parse_qs(query.query)
                return p['v'][0]
            if query.path[:7] == '/embed/':
                return query.path.split('/')[2]
            if query.path[:3] == '/v/':
                return query.path.split('/')[2]
        return None

    def _get_authenticated_service(self):
        flow = flow_from_clientsecrets(self.client_secret_filename, scope='https://www.googleapis.com/auth/youtube')

        storage = Storage(self.oauth_storage_filename)
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            parser = argparse.ArgumentParser(description=__doc__,
                                             formatter_class=argparse.RawDescriptionHelpFormatter,
                                             parents=[argparser])
            credentials = run_flow(flow, storage, parser.parse_args([]))

        return build('youtube', 'v3', http=credentials.authorize(httplib2.Http()))

    def _add_video_to_playlist(self, video_id, playlist_id=None):
        playlist_id = playlist_id or self.playlist_id
        service = self._get_authenticated_service()
        service.playlistItems().insert(
            part="snippet",
            body={
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }).execute()
