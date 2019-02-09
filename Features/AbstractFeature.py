from preferences import prefs_singleton


class AbstractFeature:

    def disable(self):
        prefs_singleton.write_value(type(self).__name__ + '_enabled', False)

    def enable(self):
        prefs_singleton.write_value(type(self).__name__ + '_enabled', True)

    def is_enabled(self):
        return prefs_singleton.read_with_default(type(self).__name__ + '_enabled', True)

    def message_filter(self, bot, source, target, message, highlighted):
        raise NotImplementedError

    @staticmethod
    def description():
        raise NotImplementedError
