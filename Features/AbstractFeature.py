from abc import ABC


class AbstractFeature(ABC):
    enabled = True

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    def is_enabled(self):
        return self.enabled

    def message_filter(self, bot, source, target, message, highlighted):
        raise NotImplementedError

    @staticmethod
    def description():
        raise NotImplementedError
