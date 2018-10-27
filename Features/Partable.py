from Features.AbstractFeature import AbstractFeature


class Partable(AbstractFeature):
    @staticmethod
    def description():
        return 'Causes the bot to part from the current channel. Must be authorized to perform. Usage: "!leave"'

    def message_filter(self, bot, source, target, message, highlighted):
        if (message == "leave" and highlighted) or message == "!leave":  # respond to !leave
            if source in bot.json_data['channels']:
                bot.json_data['channels'].remove(source)
                bot.save_json()
                bot.part(source)
            return True
        return False
