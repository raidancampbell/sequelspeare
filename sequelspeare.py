import asyncio
import importlib
from pkgutil import walk_packages

import pydle

import Features
from preferences import prefs_singleton


class SequelSpeare(pydle.Client):

    def __init__(self):
        bot_nick = prefs_singleton.read_value('botnick')
        bot_real_name = prefs_singleton.read_value('botrealname')
        server_address = prefs_singleton.read_value('serveraddress')
        server_port = int(prefs_singleton.read_value('serverport'))
        self.channels_ = prefs_singleton.read_value('channels')
        self.PING_TIMEOUT = 185
        self.RECONNECT_MAX_ATTEMPTS = None  # always try to reconnect

        super().__init__(bot_nick, realname=bot_real_name)
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.connect(server_address, server_port, tls=False, tls_verify=False), loop=loop)

        self.preferences = prefs_singleton

        self.blacklist = ['AbstractFeature', 'Intelligence', 'Renameable', 'Remindable']
        self.plugins = self.load_features(self.blacklist)

        # brain is just an instance so it can be referenced again
        if prefs_singleton.read_with_default('Intelligence_enabled', True):
            from Features.Intelligence import Intelligence
            brain = Intelligence()
            self.plugins.append(brain)
            # renameable needs intelligence to rename itself
            if prefs_singleton.read_with_default('Renameable_enabled', True):
                from Features.Renameable import Renameable
                self.plugins.append(Renameable(brain))
        # Remindable needs access to the bot, so it can send a line at any time
        if prefs_singleton.read_with_default('Remindable_enabled', True):
            from Features.Remindable import Remindable
            self.plugins.append(Remindable(self))

        self.plugins.sort(key=lambda f: f.priority)
        loop.run_forever()

    async def disconnect_with_reconnect(self):
        try:
            await self._disconnect(False)
        except OSError as e:
            print('exception while reconnecting: ' + str(type(e)) + str(e))
            print('rescheduling ping checker...')
            print('connection retries and timeouts will be lost.')
            if self._ping_checker_handle:
                self._ping_checker_handle.cancel()
            self._ping_checker_handle = self.eventloop.create_task(
                self._perform_ping_timeout(self.PING_TIMEOUT))

    async def on_data_error(self, exception):
        self.logger.error('Encountered error on socket.', exc_info=(type(exception), exception, None))
        if type(exception) == TimeoutError:
            await self.disconnect_with_reconnect()
        else:
            await self.disconnect(expected=False)

    async def on_connect(self):
        print('joined network')
        await super().on_connect()
        # connect to all the channels we want to
        for channel in self.channels_:
            await self.join(channel)

    # ignore "X is now your displayed host" messages
    async def on_raw_396(self, _):
        pass

    # when the bot is invited to a channel, respond by joining the channel
    async def on_invite(self, dest_channel, inviter):
        print(f'invited to {dest_channel} by {inviter}')
        self.join(dest_channel)
        if dest_channel not in self.preferences.read_value('channels'):
            self.preferences.write_value('channels', self.preferences.read_value('channels').append(dest_channel))

    # when a message is received, figure out if the bot itself was pinged, and execute the plugin chain appropriately
    async def on_message(self, source, target, message):
        cleaned_message = message.split(':', 1)
        # if someone sent a line saying 'nick: command'
        if len(cleaned_message) > 1 and cleaned_message[0].lower() == self.nickname:
            # split an trim it to get 'command'
            await self.run_plugins(source, target, cleaned_message[1].strip(), highlighted=True)
        else:
            await self.run_plugins(source, target, message.strip(), highlighted=False)

    # chain the message through all the plugins. Each plugin has the option to continue or kill the chain
    async def run_plugins(self, source, target, message, highlighted):
        enabled_plugins = (plugin for plugin in self.plugins if plugin.is_enabled())
        for plugin in enabled_plugins:
            try:
                stop_chain = await plugin.message_filter(bot=self, source=source, target=target, message=message, highlighted=highlighted)
                if stop_chain:
                    break
            # exceptions in filters are considered benign. log and continue
            except Exception as e:
                print(e)

    @staticmethod
    def _find_features():
        for _, name, is_pkg in walk_packages(Features.__path__, prefix='Features.'):
            if not is_pkg:
                yield name

    @staticmethod
    def load_features(blacklist):
        enabled_features = []

        for module_name in SequelSpeare._find_features():
            class_name = module_name.split('.')[-1]
            if prefs_singleton.read_with_default(f'{class_name}_enabled', True) and class_name not in blacklist:
                module = importlib.import_module(module_name)
                clazz = getattr(module, class_name)
                enabled_features.append(clazz())
        return enabled_features

    @staticmethod
    def reload_features(blacklist, existing_features):
        existing_features_str = []
        reloaded_features = []
        # existing features need to be reloaded
        for feature in existing_features:
            existing_features_str.append(type(feature).__name__)

        for module_name in SequelSpeare._find_features():
            class_name = module_name.split('.')[-1]
            # if the module is enabled, and not blacklisted, and already loaded:
            if prefs_singleton.read_with_default(f'{class_name}_enabled', True) and class_name not in blacklist and class_name:
                for feature in existing_features:
                    if type(feature).__name__ == module_name:
                        # reload it and re-instantiate it
                        importlib.reload(feature)
                module = importlib.import_module(module_name)
                clazz = getattr(module, class_name)
                reloaded_features.append(clazz())
            # if the module is enabled, and not blacklisted, but has not already been loaded:
            elif prefs_singleton.read_with_default(f'{class_name}_enabled', True) and class_name not in blacklist and class_name not in existing_features_str:
                # import it and instantiate it
                module = importlib.import_module(module_name)
                clazz = getattr(module, class_name)
                reloaded_features.append(clazz())
        return reloaded_features


# Execution begins here, if called via command line
if __name__ == '__main__':
    SequelSpeare()
