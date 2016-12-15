""" The known commands are:

    ping -- Pongs the user

    source -- gives a link to the source code

    leave -- makes the bot part the channel

    die -- Let the bot cease to exist.
"""

import irc.bot
import irc.strings
import argparse  # parse strings from CLI invocation
import json
import re
from sample import Sampler
from jaraco.stream import buffer


class SequelSpeare(irc.bot.SingleServerIRCBot):
    def __init__(self, json_filename):
        self.json_filename = json_filename
        with open(json_filename, 'r') as infile:
            self.json_data = json.loads(infile.read())
        irc.bot.SingleServerIRCBot.__init__(self, [(self.json_data['serveraddress'], self.json_data['serverport'])],
                                            self.json_data['botnick'], self.json_data['botrealname'])
        self.connection.buffer_class = buffer.LenientDecodingLineBuffer
        self.channels_ = self.json_data['channels']
        try:
            self.hiss_whitelist = self.json_data['whitelistnicks']
        except KeyError:
            self.hiss_whitelist = []
            self.json_data['whitelistnicks'] = []
            self.save_json()
        self.connection.add_global_handler('invite', self.on_invite)
        self.sampler = Sampler()

    # when the bot is invited to a channel, respond by joining the channel
    def on_invite(self, connection, event):
        channel_to_join = event.arguments[0]
        connection.join(channel_to_join)
        if channel_to_join not in self.json_data['channels']:
            self.json_data['channels'].append(channel_to_join)
            self.save_json()

    def save_json(self):
        with open(self.json_filename, 'w') as outfile:
            # write the json to the file, pretty-printed with indentations, and alphabetically sorted
            json.dump(self.json_data, outfile, indent=2, sort_keys=True)

    # if the nick is already taken, append an underscore
    @staticmethod
    def on_nicknameinuse(connection, event):
        connection.nick(connection.get_nickname() + "_")

    # whenever we're finished connecting to the server, join the channels
    def on_welcome(self, connection, event):
        # connect to all the channels we want to
        for chan in self.channels_:
            connection.join(chan)

    # log private messages to stdout, and try to parse a command from it
    def on_privmsg(self, connection, event):
        message_text = event.arguments[0]
        print('PRIV: <' + event.source.nick + '> ' + message_text)
        # TODO: keep this from triggering itself.
        # self.do_command(event, message_text)

    # log public messages to stdout, hiss on various conditions, and try to parse a command
    def on_pubmsg(self, connection, event):
        message_text = event.arguments[0]
        a = message_text.split(":", 1)
        # if someone sent a line saying "mynick: command"
        if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
            # split an trim it to get "command"
            self.do_command(event, a[1].strip())
        elif message_text.startswith('!'):
            self.do_command(event, message_text.strip())
        if event.source.nick not in self.hiss_whitelist:
            message_text = message_text.lower()
            # hiss at buzzfeed/huffpost, characters greater than 128, and on the word 'moist'
            if 'buzzfeed.com' in message_text or 'huffingtonpost.com' in message_text:
                connection.privmsg(event.target, 'hisss fuck off with your huffpost buzzfeed crap')
            elif not all(ord(c) < 128 for c in event.arguments[0]) or 'moist' in message_text:
                connection.privmsg(event.target, 'hisss')
        print('PUB: <' + event.source.nick + '> ' + event.arguments[0])

    # performs the various commands documented at the top of the file
    def do_command(self, event, cmd_text):
        connection = self.connection

        if cmd_text == "leave" or cmd_text == "!leave":  # respond to !leave
            if event.target in self.json_data['channels']:
                self.json_data['channels'].remove(event.target)
                self.save_json()
            connection.part(event.target)
        elif cmd_text == "die" or cmd_text == "!die":  # respond to !die
            if event.source.nick == self.json_data['botownernick']:
                print('received authorized request to die. terminating...')
                self.die()
                exit(0)
            else:
                print('received unauthorized request to die. Ignoring')
                connection.privmsg(event.target,
                                   event.source.nick + ": you're not " + self.json_data['botownernick'] + '!')
        elif cmd_text == "ping" or cmd_text == "!ping":  # respond to !ping
            connection.privmsg(event.target, event.source.nick + ': ' + "Pong!")
        elif cmd_text == "source" or cmd_text == "!source":  # respond to !source
            connection.privmsg(event.target,
                               event.source.nick + ': ' + "https://github.com/raidancampbell/sequelspeare")
        elif cmd_text == "rename" or cmd_text == "!rename":
            self.apply_new_nick(self.generate_new_nick())
        else:  # query the network with the text
            response = self.query_network(event.source.nick, cmd_text)
            connection.privmsg(event.target, event.source.nick + ': ' + response)

    def query_network(self, nick, line):
        network_input = nick + ' ' + line + '\n'  # structure the input to be identical to the training data
        response, is_err = self.sampler.sample(prime_text=network_input)  # remember, the sampler will prepend your input to the response

        is_formatted_as_expected = (response and  # did we get a response from the network
                                    len(response.split('\n')) > 1 and  # is there more than one line (i.e. the network said something)
                                    response.split('\n')[1] and  # does the first line of the network's response have any content
                                    (response.split('\n')[1]).split(' ')[1:])  # is there more content than just an empty nick

        while not is_formatted_as_expected:
            if is_err:
                return 'something went wrong...'
            response, is_err = self.sampler.sample(prime_text=network_input)
            is_formatted_as_expected = response and len(response.split('\n')) > 1 and \
                                       response.split('\n')[1] and ' '.join((response.split('\n')[1]).split(' ')[1:]).strip()

        print('responding to query with: ' + ' '.join((response.split('\n')[1]).split(' ')[1:]).strip())
        # the first line is the input.  The second line is the first line of the response
        # the first word of the second line is a nickname.  Strip the nick and write the second line.
        return ' '.join((response.split('\n')[1]).split(' ')[1:]).strip()

    def generate_new_nick(self):
        network_input = 'swiggity'
        response, is_err = self.sampler.sample(prime_text=network_input, sample_style=Sampler.SAMPLE_EACH_TIMESTEP)
        if is_err:
            return 'swiggity'
        nick_regex = '[a-zA-Z][a-zA-Z0-9_|-]+'
        new_nick = re.match(nick_regex, response).group(0)
        return new_nick if len(new_nick) <= 30 else new_nick[:30]

    def apply_new_nick(self, new_nick):
        print('changing nick to: ' + new_nick)
        self.connection.nick(new_nick)


# parse args from command line invocation
def parse_args():
    parser = argparse.ArgumentParser(description="runs the sequelspeare IRC bot")
    parser.add_argument('--json_filename', type=str, help="Filename of the json configuration file [sequelspeare.json]",
                        required=False)
    return parser.parse_args()


# Execution begins here, if called via command line
if __name__ == '__main__':
    args = parse_args()
    json_filename_ = args.json_filename or 'sequelspeare.json'
    bot = SequelSpeare(json_filename=json_filename_)
    bot.start()
