from Features.AbstractFeature import AbstractFeature


class Slappable(AbstractFeature):
    @staticmethod
    def description():
        return 'Slaps the given user. Usage: "!slap <user>"'

    async def message_filter(self, bot, source, target, message, highlighted):
        if (message.startswith('slap') and highlighted) or message.startswith('!slap'):
            slap_target = message[message.index('slap ')+4:].strip()
            await bot.ctcp(source, f'ACTION slaps {slap_target} around a bit with a large trout', '')
            return True
        return False
