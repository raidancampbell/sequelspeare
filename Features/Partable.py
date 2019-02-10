from Features.AbstractFeature import AbstractFeature
from preferences import prefs_singleton


class Partable(AbstractFeature):
    @staticmethod
    def description():
        return 'Causes the bot to part from the current channel. Must be authorized to perform. Usage: "!leave"'

    async def message_filter(self, bot, source, target, message, highlighted):
        if (message == 'leave' and highlighted) or message == '!leave':  # respond to !leave
            if source in prefs_singleton.read_value('channels'):
                prefs_singleton.write_value(prefs_singleton.read_value('channels').remove(source))
                await bot.part(source)
            return True
        return False
