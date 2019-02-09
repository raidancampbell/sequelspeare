from Features.AbstractFeature import AbstractFeature


class Killable(AbstractFeature):
    @staticmethod
    def description():
        return 'Disconnects the bot from the IRC server and terminates. Must be authorized to perform. Usage: "!die"'

    def message_filter(self, bot, source, target, message, highlighted):
        if message == 'die' or message == '!die':  # respond to !die
            if target == bot.preferences.read_value('botownernick'):
                print('received authorized request to die. terminating...')
                bot.reminder_timer.stop()
                bot.rename_timer.stop()
                bot.disconnect()
                exit(0)
            else:
                print('received unauthorized request to die. Ignoring')
                bot.message(source, "{}: you're not {}!".format(target, bot.preferences.read_value('botownernick')))
            return True
        return False
