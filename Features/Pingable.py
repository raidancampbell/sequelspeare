from Features.AbstractFeature import AbstractFeature


class Pingable(AbstractFeature):
    def message_filter(self, bot, source, target, message, highlighted):
        if message == "ping" or message == "!ping":  # respond to !ping
            bot.message(source, '{}: Pong!'.format(target))
            return True
        return False
