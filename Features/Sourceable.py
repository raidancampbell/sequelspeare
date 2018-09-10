from Features.AbstractFeature import AbstractFeature


class Sourceable(AbstractFeature):
    def message_filter(self, bot, source, target, message, highlighted):
        if message == "source" or message == "!source":  # respond to !source
            bot.message(source, '{}: https://github.com/raidancampbell/sequelspeare'.format(target))
            return True
        return False
