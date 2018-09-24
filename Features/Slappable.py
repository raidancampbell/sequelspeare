from Features.AbstractFeature import AbstractFeature


class Slappable(AbstractFeature):
    @staticmethod
    def description():
        return 'Slaps the given user. Usage: "!slap <user>"'

    def message_filter(self, bot, source, target, message, highlighted):
        if (message.startswith("slap") and highlighted) or message.startswith("!slap"):
            slap_target = message[message.index('slap ')+4:].strip()
            bot.ctcp(source, 'ACTION slaps {} around a bit with a large trout'.format(slap_target), '')
            return True
        return False
