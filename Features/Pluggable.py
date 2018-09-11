from Features.AbstractFeature import AbstractFeature


class Pluggable(AbstractFeature):
    def message_filter(self, bot, source, target, message, highlighted):
        return Pluggable.control_plugins(bot, source, target, message) or Pluggable.plugin_status(bot, source, target, message)

    @staticmethod
    def control_plugins(bot, source, target, message):
        if not (message.startswith("disable") or message.startswith("!disable")
                or message.startswith("enable") or message.startswith("!enable")
                or message.startswith("toggle") or message.startswith("!toggle")):
            return False
        request_type = message.split()[0].lower().strip()
        if request_type.startswith('!'):
            request_type = request_type[1:]

        if len(message.split()) < 2:
            request = ''
        else:
            request = message.split()[1].lower().strip()

        if target != bot.json_data['botownernick']:
            bot.message(source, "{}: you're not {}!".format(target, bot.json_data['botownernick']))
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
                bot.message(source, "{} enabled, now: {}".format(plugin_name, str(plugin.enabled).upper()))
                break
        else:
            bot.message(source, 'no plugin named "{}" was found!'.format(request))
        return True

    @staticmethod
    def plugin_status(bot, source, target, message):
        if not (message.startswith("status") or message.startswith("!status")):
            return False
        request_type = message.split()[0].lower().strip()
        if request_type.startswith('!'):
            request_type = request_type[1:]

        if len(message.split()) < 2:
            request = ''
        else:
            request = message.split()[1].lower().strip()

        if request_type == 'status':
            for plugin in bot.plugins:
                plugin_name = type(plugin).__name__.lower()
                if plugin_name == request or not request:
                    bot.message(source, "{} enabled: {}".format(plugin_name, str(plugin.enabled).upper()))
        return True
