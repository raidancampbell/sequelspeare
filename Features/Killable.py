from Features.AbstractFeature import AbstractFeature


class Killable(AbstractFeature):
    def message_filter(self, bot, source, target, message, highlighted):
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
