from Features.AbstractFeature import AbstractFeature
from threading import Timer
import time
import random


class Remindable(AbstractFeature):
    @staticmethod
    def description():
        return 'Stores a message and reminds the user after a given amount of time.  ' \
               'Usage: "!remind [in] 5 (second[s]/minute[s]/hour[s]/day[s]/random) reminder text"'

    def __del__(self):
        self.reminder_timer.stop()

    def __init__(self, bot):
        self.reminder_timer = RepeatedTimer(5, Remindable.check_reminders, self)
        self.reminder_timer.start()
        self.bot = bot

    def message_filter(self, bot, source, target, message, highlighted):
        if (message.startswith('remind') and highlighted) or message.startswith('!remind'):  # respond to !remind
            if target not in bot.hiss_whitelist:
                wait_time, reminder_text = Remindable.parse_remind(message)
                if reminder_text:
                    bot.message(source, target + ": I'll remind you about " + reminder_text)
                    reminder_object = {'channel': source, 'remindertext': f'{target}: {reminder_text}',
                                       'remindertime': int(time.time()) + wait_time}
                    bot.preferences.write_value('reminders', bot.preferences.read_value('reminders').append(reminder_object))
                else:
                    bot.message(source, target + ': Usage is "!remind [in] 5 (second[s]/minute[s]/hour[s]/day[s]) '
                                                 'reminder text"')
            return True
        return False

    # rereads the reminders, then issues them as needed
    def check_reminders(self):
        for reminder_object in self.bot.preferences.read_value('reminders'):  # check the reminders
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
                        print(f'ERR: failed to parse: {word} into a float!')
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
        remaining_reminders = list(filter(lambda x: x['remindertime'] != kwargs['remindertime'], kwargs['bot'].preferences.read_value('reminders')))
        kwargs['bot'].preferences.write_value('reminders', remaining_reminders)


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
