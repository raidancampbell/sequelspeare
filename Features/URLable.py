from Features.AbstractFeature import AbstractFeature
import validators
import urllib.request
import ssl
from bs4 import BeautifulSoup


class URLable(AbstractFeature):

    @staticmethod
    def description():
        return 'Passively retrieves each URL posted, and provides the HTML Title as a summary of the link'

    def __init__(self):
        self.no_ssl = ssl._create_unverified_context()

    def message_filter(self, bot, source, target, message, highlighted):
        url = self.extract_url(message)
        if url:
            try:
                soup = BeautifulSoup(urllib.request.urlopen(url, context=self.no_ssl), "html.parser")
                bot.message(source, soup.title.string.split('\n')[0])
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
