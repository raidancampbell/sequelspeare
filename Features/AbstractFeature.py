from abc import ABC


class AbstractFeature(ABC):
    enabled = True

    def message_filter(self, bot, source, target, message, highlighted):
        raise NotImplementedError

    @staticmethod
    def description():
        raise NotImplementedError
