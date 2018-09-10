from Features.AbstractFeature import AbstractFeature


class Loggable(AbstractFeature):
    def message_filter(self, bot, source, target, message, highlighted):
        print('{}: <{}> {}'.format(source, target, message))
        return False
