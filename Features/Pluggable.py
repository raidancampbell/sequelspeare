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
        if await Pluggable.reload(bot, source, target, message, highlighted):
            return True
        return False

    @staticmethod
    async def reload(bot, source, target, message, highlighted):
        if not ((message.startswith('reload') and highlighted) or message.startswith('!reload')):
            return False
        prefs_singleton.reload_from_disk()

        reloaded_features = bot.reload_features(blacklist=bot.blacklist, existing_features=bot.plugins)
        old_str = [type(feature).__name__ for feature in bot.plugins]
        new_str = [type(feature).__name__ for feature in reloaded_features]

        new_features = set(new_str).difference(set(old_str))

        for feature in bot.plugins:
            if type(feature).__name__ not in bot.blacklist:
                bot.plugins.remove(feature)
        bot.plugins.extend(reloaded_features)
        bot.plugins.sort(key=lambda f: f.priority)

        if new_features:
            await bot.message(source, f'plugins reloaded. new plugin[s] [{",".join(new_features)}] were imported')
        else:
            await bot.message(source, f'plugins reloaded. No new plugins imported')

        return True

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
