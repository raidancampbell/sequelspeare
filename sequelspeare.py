import asyncio

import pydle

from preferences import prefs_singleton
from Features.Wolframable import Wolframable
from Features.Calculable import Calculable
from Features.Killable import Killable
from Features.Partable import Partable
from Features.Hissable import Hissable
from Features.Intelligence import Intelligence
from Features.Loggable import Loggable
from Features.Pingable import Pingable
from Features.Pluggable import Pluggable
from Features.Printable import Printable
from Features.Remindable import Remindable
from Features.Renameable import Renameable
from Features.Slappable import Slappable
from Features.Sourceable import Sourceable
from Features.URLable import URLable
from Features.Youtubable import Youtubable


class SequelSpeare(pydle.Client):

    def __init__(self):
        bot_nick = prefs_singleton.read_value('botnick')
        bot_real_name = prefs_singleton.read_value('botrealname')
        server_address = prefs_singleton.read_value('serveraddress')
        server_port = int(prefs_singleton.read_value('serverport'))
        self.channels_ = prefs_singleton.read_value('channels')

        super().__init__(bot_nick, realname=bot_real_name)
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.connect(server_address, server_port, tls=False, tls_verify=False), loop=loop)

        self.preferences = prefs_singleton
        brain = Intelligence()
        self.plugins = [Loggable(), Printable(), Pluggable(), Partable(), Killable(), Pingable(), Sourceable(),
                        Remindable(self),  # Remindable needs access to the bot, so it can send a line at any time
                        brain,  # brain is just an instance so it can be referenced again
                        Renameable(brain),  # renameable needs intelligence to rename itself
                        Hissable(), URLable(), Slappable(), Calculable(), Wolframable(), Youtubable()]

        loop.run_forever()

    async def on_connect(self):
        print('joined network')
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


# Execution begins here, if called via command line
if __name__ == '__main__':
    SequelSpeare()
