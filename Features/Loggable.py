from Features.AbstractFeature import AbstractFeature


class Loggable(AbstractFeature):
    @staticmethod
    def description():
        return 'Passively logs all messages the bot sees to stdout.'

    def message_filter(self, bot, source, target, message, highlighted):
        print(f'{source}: <{target}> {message}')
        return False
