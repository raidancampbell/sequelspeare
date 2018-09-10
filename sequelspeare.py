""" The known commands are:

    ping -- Pongs the user

    source -- gives a link to the source code

    leave -- makes the bot part the channel

    die -- Let the bot cease to exist.

    rename -- allows the bot to choose its own nick
"""
from abc import ABC

import pydle
import argparse  # parse strings from CLI invocation
import json
import re
import random  # for !remind random
import time  # unix timestamp is `int(time.time())`
from threading import Timer
try:
    from sample import Sampler
except ImportError:
    pass


# thanks, http://stackoverflow.com/a/13151299/3006365
class RepeatedTimer(object):
    def __init__(self, interval, _function, *_args, **kwargs):
        self._timer = None
        self.function = _function
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


class BotFeature(ABC):
    @staticmethod
    def message_filter(bot, source, target, message, highlighted):
        pass


class Intelligence(BotFeature):
    def __init__(self):
        self.sampler = Sampler()
        self.sample = self.sampler.sample

    def message_filter(self, bot, source, target, message, highlighted):
        if highlighted:
            bot.message(source, target + ': ' + self.query_network(target, message))
            return True
        return False

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
            is_formatted_as_expected = response and len(response.split('\n')) > 1 and response.split('\n')[1] and ' '.join((response.split('\n')[1]).split(' ')[1:]).strip()

        print('responding to query with: ' + ' '.join((response.split('\n')[1]).split(' ')[1:]).strip())
        # the first line is the input.  The second line is the first line of the response
        # the first word of the second line is a nickname.  Strip the nick and write the second line.
        return ' '.join((response.split('\n')[1]).split(' ')[1:]).strip()


class Renameable(BotFeature):
    def __init__(self, intelligence):
        self.intelligence = intelligence

    def message_filter(self, bot, source, target, message, highlighted):
        if message == "rename" or message == "!rename":  # respond to !leave
            bot.set_nickname(self.generate_new_nick())
            return True
        return False

    def generate_new_nick(self):
        network_input = 'swiggity'
        response, is_err = self.intelligence.sample(prime_text=network_input, sample_style=Sampler.SAMPLE_EACH_TIMESTEP)
        if is_err:
            return 'swiggity'
        nick_regex = '[a-zA-Z][a-zA-Z0-9_|-]+'
        new_nick = re.match(nick_regex, response).group(0)
        return new_nick if len(new_nick) <= 30 else new_nick[:30]


class Partable(BotFeature):
    @staticmethod
    def message_filter(bot, source, target, message, highlighted):
        if message == "leave" or message == "!leave":  # respond to !leave
            if source in bot.json_data['channels']:
                bot.json_data['channels'].remove(source)
                bot.save_json()
                bot.part(source)
            return True
        return False


class Killable(BotFeature):
    @staticmethod
    def message_filter(bot, source, target, message, highlighted):
        if message == "die" or message == "!die":  # respond to !die
            if target == bot.json_data['botownernick']:
                print('received authorized request to die. terminating...')
                bot.reminder_timer.stop()
                bot.rename_timer.stop()
                bot.disconnect()
                exit(0)
            else:
                print('received unauthorized request to die. Ignoring')
                bot.message(source, "{}: you're not {}!".format(target, bot.json_data['botownernick']))
            return True
        return False


class Loggable(BotFeature):
    @staticmethod
    def message_filter(bot, source, target, message, highlighted):
        print('{}: <{}> {}'.format(source, target, message))
        return False


class Hissable(BotFeature):
    def __init__(self, hiss_whitelist):
        self.hiss_whitelist = hiss_whitelist

    def message_filter(self, bot, source, target, message, highlighted):
        if target not in self.hiss_whitelist:
            message = message.lower()
            # hiss at buzzfeed/huffpost, characters greater than 128, and on the word 'moist'
            if 'buzzfeed.com' in message or 'huffingtonpost.com' in message:
                bot.message(source, 'hisss fuck off with your huffpost buzzfeed crap')
            elif not all(ord(c) < 128 for c in message) or 'moist' in message:
                bot.message(source, 'hisss')
        return False


class Sourceable(BotFeature):
    @staticmethod
    def message_filter(bot, source, target, message, highlighted):
        if message == "source" or message == "!source":  # respond to !source
            bot.message(source, '{}: https://github.com/raidancampbell/sequelspeare'.format(target))
            return True
        return False


class Pingable(BotFeature):
    @staticmethod
    def message_filter(bot, source, target, message, highlighted):
        if message == "ping" or message == "!ping":  # respond to !ping
            bot.message(source, '{}: Pong!'.format(target))
            return True
        return False


class Remindable(BotFeature):
    def __del__(self):
        self.reminder_timer.stop()

    def __init__(self, bot):
        self.reminder_timer = RepeatedTimer(5, Remindable.check_reminders, self)
        self.reminder_timer.start()
        self.json_filename = bot.json_filename
        self.bot = bot

    @staticmethod
    def message_filter(bot, source, target, message, highlighted):
        if message.startswith("remind") or message.startswith("!remind"):  # respond to !remind
            if target not in bot.hiss_whitelist:
                wait_time, reminder_text = Remindable.parse_remind(message)
                if reminder_text:
                    bot.message(source, target + ": I'll remind you about " + reminder_text)
                    reminder_object = {'channel': source, 'remindertext': '{}: {}'.format(target, reminder_text),
                                       'remindertime': int(time.time()) + wait_time}
                    bot.json_data['reminders'].append(reminder_object)
                    bot.save_json()  # write the reminder to the file.  The background thread will pick it up and issue
                else:
                    bot.message(source, target + ': Usage is "!remind [in] 5 (second[s]/minute[s]/hour[s]/day[s]) '
                                                 'reminder text"')
            return True
        return False

    # rereads the json reminders, then issues them as needed
    def check_reminders(self):
        with open(self.json_filename, 'r') as infile:  # read the json
            json_data = json.loads(infile.read())
        for reminder_object in json_data['reminders']:  # check the reminders
            if reminder_object['remindertime'] > time.time():
                continue
            # if a reminder has expired
            reminder_object_non_serializable = reminder_object.copy()
            reminder_object_non_serializable['self'] = self
            reminder_object_non_serializable['bot'] = self.bot
            self.issue_reminder(**reminder_object_non_serializable)

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
                        print('ERR: failed to parse: {} into a float!'.format(word))
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

    # issue a reminder on the given channel to the given nick with the given text
    # kwargs should contain: 'connection', 'channel', and 'reminder_text'
    @staticmethod
    def issue_reminder(**kwargs):
        kwargs['bot'].message(kwargs['channel'], kwargs['remindertext'])
        # after issuing the reminder, remove it from the list of things to remind
        # there is a theoretical collision if multiple reminders are targeted at the same second,
        # only one may be issued then all within that second will be deleted.
        # it is more likely to have a unique remindertime than unique remindertext, so this choice is acceptable
        kwargs['bot'].json_data['reminders'] = list(
            filter(lambda x: x['remindertime'] != kwargs['remindertime'], kwargs['bot'].json_data['reminders']))
        kwargs['bot'].save_json()


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
        self.plugins = [Loggable, Partable, Killable, Pingable, Sourceable, Remindable(self), brain, Renameable(brain), Hissable(self.hiss_whitelist)]

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

    # log public messages to stdout, hiss on various conditions, and try to parse a command
    def on_message(self, source, target, message):
        cleaned_message = message.split(":", 1)
        # if someone sent a line saying "nick: command"
        if len(cleaned_message) > 1 and cleaned_message[0].lower() == self.nickname:
            # split an trim it to get "command"
            self.run_plugins(source, target, cleaned_message[1].strip(), highlighted=True)
        else:
            self.run_plugins(source, target, message.strip(), highlighted=False)

    def run_plugins(self, source, target, message, highlighted):
        for plugin in self.plugins:
            stop_chain = plugin.message_filter(bot=self, source=source, target=target, message=message, highlighted=highlighted)
            if stop_chain:
                break


# parse args from command line invocation
def parse_args():
    parser = argparse.ArgumentParser(description="runs the Sequelspeare IRC bot")
    parser.add_argument('--json_filename', type=str, help="Filename of the json configuration file [sequelspeare.json]",
                        required=False)
    return parser.parse_args()


# Execution begins here, if called via command line
if __name__ == '__main__':
    args = parse_args()
    json_filename_ = args.json_filename or 'sequelspeare.json'
    SequelSpeare.init(json_filename=json_filename_).handle_forever()
