import os
import pydle
import argparse  # parse strings from CLI invocation
import json

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


class SequelSpeare(pydle.Client):

    @staticmethod
    def init(json_filename):
        with open(json_filename, 'r') as infile:
            json_data = json.loads(infile.read())

        server_addr = json_data['serveraddress']
        server_port = json_data['serverport']
        nickname = json_data['botnick']
        realname = json_data['botrealname']
        return SequelSpeare(json_filename, server_addr, server_port, nickname, realname)

    def __init__(self, json_filename, server_addr, server_port, nickname, realname):
        super().__init__(nickname, realname=realname)
        self.connect(server_addr, int(server_port), tls=False, tls_verify=False)

        self.json_filename = json_filename
        with open(json_filename, 'r') as infile:
            self.json_data = json.loads(infile.read())

        self.channels_ = self.json_data['channels']
        self.hiss_whitelist = self.json_data['whitelistnicks']
        brain = Intelligence()
        self.plugins = [Loggable(), Printable('/dev/fake'), Pluggable(), Partable(), Killable(), Pingable(), Sourceable(), Remindable(self), brain, Renameable(brain), Hissable(self.hiss_whitelist), URLable(), Slappable(), Calculable(), Wolframable(os.getenv('WOLFRAM_KEY'))]

    def on_connect(self):
        print('joined network')
        # connect to all the channels we want to
        for channel in self.channels_:
            self.join(channel)

    def save_json(self):
        with open(self.json_filename, 'w') as outfile:
            # write the json to the file, pretty-printed with indentations, and alphabetically sorted
            json.dump(self.json_data, outfile, indent=2, sort_keys=True)

    # when the bot is invited to a channel, respond by joining the channel
    def on_invite(self, dest_channel, inviter):
        print('invited to {} by {}'.format(dest_channel, inviter))
        self.join(dest_channel)
        if dest_channel not in self.json_data['channels']:
            self.json_data['channels'].append(dest_channel)
            self.save_json()

    # when a message is received, figure out if the bot itself was pinged, and execute the plugin chain appropriately
    def on_message(self, source, target, message):
        cleaned_message = message.split(":", 1)
        # if someone sent a line saying "nick: command"
        if len(cleaned_message) > 1 and cleaned_message[0].lower() == self.nickname:
            # split an trim it to get "command"
            self.run_plugins(source, target, cleaned_message[1].strip(), highlighted=True)
        else:
            self.run_plugins(source, target, message.strip(), highlighted=False)

    # chain the message through all the plugins. Each plugin has the option to continue or kill the chain
    def run_plugins(self, source, target, message, highlighted):
        enabled_plugins = (plugin for plugin in self.plugins if plugin.enabled)
        for plugin in enabled_plugins:
            try:
                stop_chain = plugin.message_filter(bot=self, source=source, target=target, message=message, highlighted=highlighted)
                if stop_chain:
                    break
            # exceptions in filters are considered benign. log and continue
            except Exception as e:
                print(e)


# parse args from command line invocation
def parse_args():
    parser = argparse.ArgumentParser(description="runs the Sequelspeare IRC bot")
    parser.add_argument('--json_filename', type=str, help="Filename of the json configuration file [sequelspeare.json]",
                        required=False)
    return parser.parse_args()


# Execution begins here, if called via command line
if __name__ == '__main__':
    import logging

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    args = parse_args()
    json_filename_ = args.json_filename or 'sequelspeare.json'
    SequelSpeare.init(json_filename=json_filename_).handle_forever()
