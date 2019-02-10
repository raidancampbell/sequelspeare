from Features.AbstractFeature import AbstractFeature


class Loggable(AbstractFeature):
    priority = 0

    @staticmethod
    def description():
        return 'Passively logs all messages the bot sees to stdout.'

    async def message_filter(self, bot, source, target, message, highlighted):
        print(f'{source}: <{target}> {message}')
        return False
