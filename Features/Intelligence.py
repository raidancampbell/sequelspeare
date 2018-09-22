from Features.AbstractFeature import AbstractFeature
from sample import Sampler


class Intelligence(AbstractFeature):
    @staticmethod
    def description():
        return 'Queries the neural network for a response to the given input. Usage: "<botnick>: <message>"'

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
