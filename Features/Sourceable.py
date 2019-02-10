from Features.AbstractFeature import AbstractFeature


class Sourceable(AbstractFeature):
    priority = 6

    @staticmethod
    def description():
        return 'Provides a link to the source code. Usage: "!source"'

    async def message_filter(self, bot, source, target, message, highlighted):
        if (message == 'source' and highlighted) or message == '!source':  # respond to !source
            await bot.message(source, f'{target}: https://github.com/raidancampbell/sequelspeare')
            return True
        return False
