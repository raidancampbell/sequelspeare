from Features.AbstractFeature import AbstractFeature
import requests


class Calculable(AbstractFeature):
    @staticmethod
    def description():
        return 'performs calculations using api.mathjs.org.  Usage: "!calc 2+2"'

    api_url = 'http://api.mathjs.org/v4/'

    async def message_filter(self, bot, source, target, message, highlighted):
        if (message.startswith('calc') and highlighted) or message.startswith('!calc'):
            trimmed_message = message[message.index('calc ') + 4:].strip()
            params = {
                'expr': trimmed_message,
                'precision': ''
            }
            request = requests.get(Calculable.api_url, params=params, timeout=10.0)

            if request.status_code == requests.codes.ok:
                await bot.message(source, request.text)
            return True
        return False
