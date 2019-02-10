from Features.AbstractFeature import AbstractFeature
from preferences import prefs_singleton
import time
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Remindable(AbstractFeature):
    @staticmethod
    def description():
        return 'Stores a message and reminds the user after a given amount of time.  ' \
               'Usage: "!remind [in] 5 (second[s]/minute[s]/hour[s]/day[s]/random) reminder text"'

    def __del__(self):
        self.scheduler.shutdown()

    def __init__(self, bot):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(Remindable.check_reminders, trigger='interval', seconds=5, max_instances=1, coalesce=True, args=[bot])
        self.scheduler.start()
        self.hiss_whitelist = prefs_singleton.read_value('whitelistnicks')

    async def message_filter(self, bot, source, target, message, highlighted):
        if (message.startswith('remind') and highlighted) or message.startswith('!remind'):  # respond to !remind
            if target not in self.hiss_whitelist:
                wait_time, reminder_text = Remindable.parse_remind(message)
                if reminder_text:
                    await bot.message(source, target + ": I'll remind you about " + reminder_text)
                    reminder_object = {'channel': source, 'remindertext': f'{target}: {reminder_text}',
                                       'remindertime': int(time.time()) + wait_time}
                    existing_reminders = prefs_singleton.read_with_default('reminders', [])
                    existing_reminders.append(reminder_object)
                    prefs_singleton.write_value('reminders', existing_reminders)
                else:
                    await bot.message(source, target + ': Usage is "!remind [in] 5 (second[s]/minute[s]/hour[s]/day[s]) '
                                                 'reminder text"')
            return True
        return False

    @staticmethod
    async def check_reminders(bot):
        for reminder_object in prefs_singleton.read_value('reminders'):  # check the reminders
            if reminder_object['remindertime'] > time.time():
                continue
            # if a reminder has expired
            await Remindable.issue_reminder(bot, reminder_object['channel'], reminder_object['remindertext'], reminder_object['remindertime'])

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
    @staticmethod
    async def issue_reminder(bot, channel, text, reminder_time):
        print(f'issuing reminder to {channel} with value {text}')
        await bot.message(channel, text)
        # after issuing the reminder, remove it from the list of things to remind
        # there is a theoretical collision if multiple reminders are targeted at the same second,
        # only one may be issued then all within that second will be deleted.
        # it is more likely to have a unique remindertime than unique remindertext, so this choice is acceptable
        remaining_reminders = list(filter(lambda x: x['remindertime'] != reminder_time, prefs_singleton.read_value('reminders')))
        prefs_singleton.write_value('reminders', remaining_reminders or [])

