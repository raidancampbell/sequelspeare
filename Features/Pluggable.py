from collections import OrderedDict

from Features.AbstractFeature import AbstractFeature


class Pluggable(AbstractFeature):
    @staticmethod
    def description():
        return 'Provides several plugin features: status, enable, disable, and description. ' \
               'Must be authorized to enable/disable. Usage: "![status/help/enable/disable/toggle] <plugin>" '

    def message_filter(self, bot, source, target, message, highlighted):
        return Pluggable.control_plugins(bot, source, target, message, highlighted) \
               or Pluggable.plugin_status(bot, source, target, message, highlighted) \
               or Pluggable.plugin_describe(bot, source, target, message, highlighted)

    @staticmethod
    def control_plugins(bot, source, target, message, highlighted):
        if not ((message.startswith("disable") and highlighted) or message.startswith("!disable")
                or (message.startswith("enable") and highlighted) or message.startswith("!enable")
                or (message.startswith("toggle") and highlighted) or message.startswith("!toggle")):
            return False
        request_type = message.split()[0].lower().strip()
        if request_type.startswith('!'):
            request_type = request_type[1:]

        if len(message.split()) < 2:
            request = ''
        else:
            request = message.split()[1].lower().strip()

        if target != bot.preferences.read_value('botownernick'):
            bot.message(source, "{}: you're not {}!".format(target, bot.preferences.read_value('botownernick')))
            return True
        for plugin in bot.plugins:
            plugin_name = type(plugin).__name__.lower()
            if plugin_name == request:
                if request_type == 'disable':
                    plugin.enabled = False
                if request_type == 'enable':
                    plugin.enabled = True
                if request_type == 'toggle':
                    plugin.enabled = not plugin.enabled
                bot.message(source, "{} changed, now: {}".format(plugin_name, str(plugin.enabled).upper()))
                break
        else:
            bot.message(source, 'no plugin named "{}" was found!'.format(request))
        return True

    @staticmethod
    def plugin_status(bot, source, target, message, highlighted):
        if not ((message.startswith("status") and highlighted) or message.startswith("!status")):
            return False

        if len(message.split()) < 2:
            request = ''
        else:
            request = message.split()[1].lower().strip()

        status_map = OrderedDict()
        for plugin in bot.plugins:
            plugin_name = type(plugin).__name__.lower()
            if plugin_name == request or not request:
                status_map[plugin_name] = plugin.enabled

        bot.message(source, 'ENABLED: {}'.format(', '.join([key for key, value in status_map.items() if value])))
        bot.message(source, 'DISABLED: {}'.format(', '.join([key for key, value in status_map.items() if not value])))
        return True

    @staticmethod
    def plugin_describe(bot, source, target, message, highlighted):
        if not ((message.startswith("help") and highlighted) or message.startswith("!help")
                or (message.startswith("describe") and highlighted) or message.startswith("!describe")):
            return False

        if len(message.split()) < 2:
            request = ''
        else:
            request = message.split()[1].lower().strip()

        for plugin in bot.plugins:
            plugin_name = type(plugin).__name__.lower()
            if plugin_name == request or not request:
                description = plugin.description()
                break
        else:
            bot.message(source, 'no plugin named "{}" was found!'.format(request))
            return False
        bot.message(source, description)
        return True
