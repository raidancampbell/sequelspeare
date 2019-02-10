import os
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

    @staticmethod
    def init():
        server_addr = prefs_singleton.read_value('serveraddress')
        server_port = prefs_singleton.read_value('serverport')
        nickname = prefs_singleton.read_value('botnick')
        realname = prefs_singleton.read_value('botrealname')
        return SequelSpeare(server_addr, server_port, nickname, realname)

    def __init__(self, server_addr, server_port, nickname, realname):
        super().__init__(nickname, realname=realname)
        self.connect(server_addr, int(server_port), tls=False, tls_verify=False)
        self.preferences = prefs_singleton
        self.channels_ = self.preferences.read_value('channels')
        self.hiss_whitelist = self.preferences.read_value('whitelistnicks')
        brain = Intelligence()
        self.plugins = [Loggable(), Printable('/dev/fake'), Pluggable(), Partable(), Killable(), Pingable(),
                        Sourceable(), Remindable(self), brain, Renameable(brain), Hissable(self.hiss_whitelist),
                        URLable(), Slappable(), Calculable(), Wolframable(), Youtubable()]

    def on_connect(self):
        print('joined network')
        # connect to all the channels we want to
        for channel in self.channels_:
            self.join(channel)

    # when the bot is invited to a channel, respond by joining the channel
    def on_invite(self, dest_channel, inviter):
        print(f'invited to {dest_channel} by {inviter}')
        self.join(dest_channel)
        if dest_channel not in self.preferences.read_value('channels'):
            self.preferences.write_value('channels', self.preferences.read_value('channels').append(dest_channel))

    # when a message is received, figure out if the bot itself was pinged, and execute the plugin chain appropriately
    def on_message(self, source, target, message):
        cleaned_message = message.split(':', 1)
        # if someone sent a line saying 'nick: command'
        if len(cleaned_message) > 1 and cleaned_message[0].lower() == self.nickname:
            # split an trim it to get 'command'
            self.run_plugins(source, target, cleaned_message[1].strip(), highlighted=True)
        else:
            self.run_plugins(source, target, message.strip(), highlighted=False)

    # chain the message through all the plugins. Each plugin has the option to continue or kill the chain
    def run_plugins(self, source, target, message, highlighted):
        enabled_plugins = (plugin for plugin in self.plugins if plugin.is_enabled())
        for plugin in enabled_plugins:
            try:
                stop_chain = plugin.message_filter(bot=self, source=source, target=target, message=message, highlighted=highlighted)
                if stop_chain:
                    break
            # exceptions in filters are considered benign. log and continue
            except Exception as e:
                print(e)


# Execution begins here, if called via command line
if __name__ == '__main__':
    import logging

    logging.basicConfig()
    # logging.getLogger().setLevel(logging.DEBUG)

    SequelSpeare.init().handle_forever()
