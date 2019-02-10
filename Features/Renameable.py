import re

from Features.AbstractFeature import AbstractFeature


class Renameable(AbstractFeature):
    @staticmethod
    def description():
        return 'Queries the neural network for a new name for the bot. Usage: "!rename"'

    def __init__(self, intelligence):
        self.intelligence = intelligence

    async def message_filter(self, bot, source, target, message, highlighted):
        if (message == 'rename' and highlighted) or message == '!rename':
            await bot.set_nickname(self.generate_new_nick())
            return True
        return False

    def generate_new_nick(self):
        network_input = 'swiggity'
        response, is_err = self.intelligence.sample(prime_text=network_input, sample_style=self.intelligence.SAMPLE_EACH_TIMESTEP)
        if is_err:
            return 'swiggity'
        nick_regex = '[a-zA-Z][a-zA-Z0-9_|-]+'
        new_nick = re.match(nick_regex, response).group(0)
        return new_nick if len(new_nick) <= 30 else new_nick[:30]
