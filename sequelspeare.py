""" The known commands are:

    ping -- Pongs the user

    source -- gives a link to the source code

    leave -- makes the bot part the channel

    die -- Let the bot cease to exist.

    rename -- allows the bot to choose its own nick
"""

import irc.bot
import irc.strings
import argparse  # parse strings from CLI invocation
import json
import re
import random  # for !remind random
import time  # unix timestamp is `int(time.time())`
from sample import Sampler
from jaraco.stream import buffer
from threading import Timer
import signal


# thanks, http://stackoverflow.com/a/13151299/3006365
class RepeatedTimer(object):
    def __init__(self, interval, function, *_args, **kwargs):
        self._timer = None
        self.function = function
        self.interval = interval
        self._args = _args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self._args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


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
        self.timer = RepeatedTimer(5, SequelSpeare.check_reminders, self)
        self.rename_timer = RepeatedTimer(60 * 60 * 24, SequelSpeare.rename_self, self)

    # rereads the json reminders, then issues them as needed
    @staticmethod
    def check_reminders(self):
        json_filename = self.json_filename
        with open(json_filename, 'r') as infile:  # read the json
            self.json_data = json.loads(infile.read())
        for reminder_object in self.json_data['reminders']:  # check the reminders
            if reminder_object['remindertime'] > time.time():
                continue
            # if a reminder has expired
            reminder_object_non_serializable = reminder_object.copy()
            reminder_object_non_serializable['connection'] = self.connection
            reminder_object_non_serializable['self'] = self
            SequelSpeare.issue_reminder(**reminder_object_non_serializable)

    @staticmethod
    def rename_self(self):
        self.apply_new_nick(self.generate_new_nick())

    def save_json(self):
        with open(self.json_filename, 'w') as outfile:
            # write the json to the file, pretty-printed with indentations, and alphabetically sorted
            json.dump(self.json_data, outfile, indent=2, sort_keys=True)

    # when the bot is invited to a channel, respond by joining the channel
    def on_invite(self, connection, event):
        channel_to_join = event.arguments[0]
        connection.join(channel_to_join)
        if channel_to_join not in self.json_data['channels']:
            self.json_data['channels'].append(channel_to_join)
            self.save_json()

    # if the nick is already taken, append an underscore
    @staticmethod
    def on_nicknameinuse(connection, event):
        connection.nick(connection.get_nickname() + "_")

    # whenever we're finished connecting to the server, join the channels
    def on_welcome(self, connection, event):
        print('joined network')
        # connect to all the channels we want to
        for chan in self.channels_:
            connection.join(chan)
        time.sleep(1)
        self.timer.start()
        self.rename_timer.start()

    # log private messages to stdout, and try to parse a command from it
    def on_privmsg(self, connection, event):
        message_text = event.arguments[0]
        print('PRIV: <' + event.source.nick + '> ' + message_text)
        if event.source.nick != connection.get_nickname():
            event.target = event.source.nick  # hack to correctly respond to a privmsg using recycled code
            self.do_command(event, message_text)

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
                self.timer.stop()
                self.rename_timer.stop()
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
        elif cmd_text.startswith("remind") or cmd_text.startswith("!remind"):  # respond to !remind
            if event.source.nick not in self.hiss_whitelist:
                wait_time, reminder_text = self.parse_remind(cmd_text)
                if reminder_text:
                    connection.privmsg(event.target, event.source.nick + ': ' + "I'll remind you about " + reminder_text)
                    reminder_object = {'channel': event.target, 'remindertext': event.source.nick + ': ' + reminder_text,
                                       'remindertime': int(time.time()) + wait_time}
                    self.json_data['reminders'].append(reminder_object)
                    self.save_json()  # write the reminder to the file.  The background thread will pick it up and issue
                else:
                    connection.privmsg(event.target, event.source.nick + ': ' +
                                   'Usage is "!remind [in] 5 (second[s]/minute[s]/hour[s]/day[s]) reminder text"')
        elif not cmd_text.startswith("!"):  # query the network with the text
            response = self.query_network(event.source.nick, cmd_text)
            connection.privmsg(event.target, event.source.nick + ': ' + response)

    # send me the entire line, starting with !remind
    # I will give you a tuple of reminder time (in seconds), and reminder text
    # if parsing fails, expect the reminder text to be empty
    @staticmethod
    def parse_remind(text):
        wait_time = 0
        finished_parsing = False
        reminder_text = ''
        text = text[1:] if text.startswith('!') else text
        if text.lower().startswith('remind random'):
            wait_time = random.randint(1, 1000) * 60
            reminder_text = text[text.index('remind random') + len('remind random'):]
        else:
            for word in text.split(' '):
                if word.isnumeric() and not wait_time:  # we parse it into a float now, and round it at the end
                    try:  # grab the time
                        wait_time = float(word)
                    except ValueError:
                        print('ERR: failed to parse: ' + word + ' into a float!')
                        return 0, ''
                elif wait_time and not finished_parsing:  # we grabbed the time, but need the units
                    if word.lower() in ['min', 'mins', 'minute', 'minutes']:
                        wait_time *= 60
                    elif word.lower() in ['hr', 'hrs', 'hours', 'hour']:
                        wait_time *= 60 * 60
                    elif word.lower() in ['day', 'days']:
                        wait_time = wait_time * 24 * 60 * 60
                    finished_parsing = True
                elif finished_parsing:
                    reminder_text += word + ' '
        return int(round(wait_time)), reminder_text.strip()  # round the time back from a float into an int

    def query_network(self, nick, line):
        network_input = nick + ' ' + line + '\n'  # structure the input to be identical to the training data
        response, is_err = self.sampler.sample(prime_text=network_input, sample_style=Sampler.SAMPLE_EACH_TIMESTEP)
        # remember, the sampler will prepend your input to the response

        is_formatted_as_expected = (response and  # did we get a response from the network
                                    len(response.split('\n')) > 1 and  # is there more than one line (i.e. the network said something)
                                    response.split('\n')[1] and  # does the first line of the network's response have any content
                                    (response.split('\n')[1]).split(' ')[1:])  # is there more content than just an empty nick

        while not is_formatted_as_expected:
            if is_err:
                return 'something went wrong...'
            response, is_err = self.sampler.sample(prime_text=network_input, sample_style=Sampler.SAMPLE_EACH_TIMESTEP)
            is_formatted_as_expected = response and len(response.split('\n')) > 1 and \
                                       response.split('\n')[1] and ' '.join((response.split('\n')[1]).split(' ')[1:]).strip()

        print('responding to query with: ' + ' '.join((response.split('\n')[1]).split(' ')[1:]).strip())
        # the first line is the input.  The second line is the first line of the response
        # the first word of the second line is a nickname.  Strip the nick and write the second line.
        return ' '.join((response.split('\n')[1]).split(' ')[1:]).strip()

    # issue a reminder on the given channel to the given nick with the given text
    # kwargs should contain: 'connection', 'channel', and 'reminder_text'
    @staticmethod
    def issue_reminder(**kwargs):
        kwargs['connection'].privmsg(kwargs['channel'], kwargs['remindertext'])
        # after issuing the reminder, remove it from the list of things to remind
        # there is a theoretical collision if multiple reminders are targeted at the same second,
        # only one may be issued then all within that second will be deleted.
        # it is more likely to have a unique remindertime than unique remindertext, so this choice is acceptable
        kwargs['self'].json_data['reminders'] = list(
            filter(lambda x: x['remindertime'] != kwargs['remindertime'], kwargs['self'].json_data['reminders']))
        kwargs['self'].save_json()

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
    # clever trick to prevent threads from surviving past the parents death
    # thanks, http://stackoverflow.com/questions/24169893/how-to-prevent-exception-ignored-in-module-threading-from-while-settin
    while True:
        signal.pause()
