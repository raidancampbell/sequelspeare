import requests

from Features.AbstractFeature import AbstractFeature
from contextlib import closing
import validators
from bs4 import BeautifulSoup


class URLable(AbstractFeature):
    MAX_RECV = 1000000

    @staticmethod
    def description():
        return 'Passively retrieves each URL posted, and provides the HTML Title as a summary of the link'

    async def message_filter(self, bot, source, target, message, highlighted):
        url = self.extract_url(message)
        if url:
            try:
                title = URLable.get_title(url)
                await bot.message(source, title)
            except Exception:
                pass
        return False

    @staticmethod
    def extract_url(string):
        for word in string.split():
            try:
                result = validators.url(word)
                if result:
                    return word
            except Exception:
                pass
        return False

    @staticmethod
    def get_title(url):
        with closing(requests.get(url, stream=True, timeout=3)) as response:
            response.raise_for_status()
            content = response.raw.read(URLable.MAX_RECV + 1, decode_content=True)
            # Sites advertising ISO-8859-1 are often lying
            if response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'
            encoding = response.encoding

        if len(content) > URLable.MAX_RECV:
            return

        html = BeautifulSoup(content, 'lxml', from_encoding=encoding)

        if html.title:
            return ' '.join(html.title.text.strip().splitlines())
