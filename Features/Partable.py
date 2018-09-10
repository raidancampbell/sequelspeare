from Features.AbstractFeature import AbstractFeature


class Partable(AbstractFeature):
    def message_filter(self, bot, source, target, message, highlighted):
        if message == "leave" or message == "!leave":  # respond to !leave
            if source in bot.json_data['channels']:
                bot.json_data['channels'].remove(source)
                bot.save_json()
                bot.part(source)
            return True
        return False
