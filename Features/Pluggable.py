from collections import OrderedDict
from preferences import prefs_singleton
from Features.AbstractFeature import AbstractFeature


class Pluggable(AbstractFeature):
    priority = 2

    @staticmethod
    def description():
        return 'Provides several plugin features: status, enable, disable, and description. ' \
               'Must be authorized to enable/disable. Usage: "![status/help/enable/disable/toggle] <plugin>" '

    async def message_filter(self, bot, source, target, message, highlighted):
        if await Pluggable.control_plugins(bot, source, target, message, highlighted):
            return True
        if await Pluggable.plugin_status(bot, source, target, message, highlighted):
            return True
        if await Pluggable.plugin_describe(bot, source, target, message, highlighted):
            return True
        return False

    @staticmethod
    async def control_plugins(bot, source, target, message, highlighted):
        if not ((message.startswith('disable') and highlighted) or message.startswith('!disable')
                or (message.startswith('enable') and highlighted) or message.startswith('!enable')
                or (message.startswith('toggle') and highlighted) or message.startswith('!toggle')):
            return False
        request_type = message.split()[0].lower().strip()
        if request_type.startswith('!'):
            request_type = request_type[1:]

        if len(message.split()) < 2:
            request = ''
        else:
            request = message.split()[1].lower().strip()

        if target != prefs_singleton.read_value('botownernick'):
            await bot.message(source, f"{target}: you're not {prefs_singleton.read_value('botownernick')}!")
            return True
        for plugin in bot.plugins:
            plugin_name = type(plugin).__name__.lower()
            if plugin_name == request:
                if request_type == 'disable':
                    plugin.disable()
                if request_type == 'enable':
                    plugin.enable()
                if request_type == 'toggle':
                    if plugin.is_enabled():
                        plugin.disable()
                    else:
                        plugin.enable()
                await bot.message(source, f'{plugin_name} changed, now: {str(plugin.is_enabled()).upper()}')
                break
        else:
            await bot.message(source, f'no plugin named "{request}" was found!')
        return True

    @staticmethod
    async def plugin_status(bot, source, target, message, highlighted):
        if not ((message.startswith('status') and highlighted) or message.startswith('!status')):
            return False

        if len(message.split()) < 2:
            request = ''
        else:
            request = message.split()[1].lower().strip()

        status_map = OrderedDict()
        for plugin in bot.plugins:
            plugin_name = type(plugin).__name__.lower()
            if plugin_name == request or not request:
                status_map[plugin_name] = plugin.is_enabled()

        await bot.message(source, f'ENABLED: {", ".join([key for key, value in status_map.items() if value])}')
        await bot.message(source, f'DISABLED: {", ".join([key for key, value in status_map.items() if not value])}')
        return True

    @staticmethod
    async def plugin_describe(bot, source, target, message, highlighted):
        if not ((message.startswith('help') and highlighted) or message.startswith('!help')
                or (message.startswith('describe') and highlighted) or message.startswith('!describe')):
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
            await bot.message(source, f'no plugin named "{request}" was found!')
            return False
        await bot.message(source, description)
        return True
