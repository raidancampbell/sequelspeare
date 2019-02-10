from Features.AbstractFeature import AbstractFeature
from preferences import prefs_singleton


class Killable(AbstractFeature):
    @staticmethod
    def description():
        return 'Disconnects the bot from the IRC server and terminates. Must be authorized to perform. Usage: "!die"'

    async def message_filter(self, bot, source, target, message, highlighted):
        if message == 'die' or message == '!die':  # respond to !die
            if target == prefs_singleton.read_value('botownernick'):
                print('received authorized request to die. terminating...')
                await bot.disconnect()
                exit(0)
            else:
                print('received unauthorized request to die. Ignoring')
                await bot.message(source, f"{target}: you're not {prefs_singleton.read_value('botownernick')}!")
            return True
        return False
