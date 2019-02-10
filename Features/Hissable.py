from Features.AbstractFeature import AbstractFeature
from preferences import prefs_singleton


class Hissable(AbstractFeature):
    @staticmethod
    def description():
        return 'Passively hisses at characters outside the lower 128, and other trigger words'

    def __init__(self):
        self.hiss_whitelist = prefs_singleton.read_value('whitelistnicks')

    async def message_filter(self, bot, source, target, message, highlighted):
        if target not in self.hiss_whitelist:
            message = message.lower()
            # hiss at buzzfeed/huffpost, characters greater than 128, and on the word 'moist'
            if 'buzzfeed.com' in message or 'huffingtonpost.com' in message:
                await bot.message(source, 'hisss fuck off with your huffpost buzzfeed crap')
            elif not all(ord(c) < 128 for c in message) or 'moist' in message:
                await bot.message(source, 'hisss')
        return False
