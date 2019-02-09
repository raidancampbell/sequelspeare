from Features.AbstractFeature import AbstractFeature


class Pingable(AbstractFeature):
    @staticmethod
    def description():
        return 'Pongs back. Useful for diagnosing a connection Usage: "!ping"'

    def message_filter(self, bot, source, target, message, highlighted):
        if message == 'ping' or message == '!ping':  # respond to !ping
            bot.message(source, f'{target}: Pong!')
            return True
        return False
