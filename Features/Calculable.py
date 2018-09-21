from Features.AbstractFeature import AbstractFeature
import requests


class Calculable(AbstractFeature):
    api_url = 'http://api.mathjs.org/v1/'

    def message_filter(self, bot, source, target, message, highlighted):
        if (message.startswith("calc") and highlighted) or message.startswith("!calc"):  # respond to !remind
            trimmed_message = message[message.index('calc ') + 4:].strip()
            params = {
                'expr': trimmed_message,
                'precision': ''
            }
            request = requests.get(Calculable.api_url, params=params, timeout=10.0)

            if request.status_code == requests.codes.ok:
                bot.message(source, request.text)
            return True
        return False
