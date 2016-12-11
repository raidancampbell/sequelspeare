import tensorflow as tf
import os
from six.moves import cPickle
from model import Model


# This object creates a TF session: you will run into issues if you instantiate it while training
# To sample some text from it, instantiate the object, and call sample(), setting the priming text and number of symbols as necessary
class Sampler:

    SAVE_DIR = 'savedata'
    PRIME_TEXT = 'swiggity'
    NUM_SAMPLE_SYMBOLS = 140
    SAMPLE_TIMESTEP_MAX = 0
    SAMPLE_EACH_TIMESTEP = 1
    SAMPLE_ON_SPACES = 2

    def __init__(self, save_dir=SAVE_DIR, prime_text=PRIME_TEXT, num_sample_symbols=NUM_SAMPLE_SYMBOLS, sample_style=SAMPLE_EACH_TIMESTEP):
        self.save_dir = save_dir
        self.prime_text = prime_text
        self.num_sample_symbols = num_sample_symbols
        self.sample_style = sample_style
        with open(os.path.join(Sampler.SAVE_DIR, 'chars_vocab.pkl'), 'rb') as file:
            self.chars, self.vocab = cPickle.load(file)
            self.model = Model(len(self.chars), is_sampled=True)
            self.sess = tf.Session()
            tf.initialize_all_variables().run(session=self.sess)
            self.checkpoint = tf.train.get_checkpoint_state(self.save_dir)
            if self.checkpoint and self.checkpoint.model_checkpoint_path:
                tf.train.Saver(tf.all_variables()).restore(self.sess, self.checkpoint.model_checkpoint_path)

    def __del__(self):
        self.sess.close()

    # returns the resultant string, isError tuple
    def sample(self, prime_text=None, num_sample_symbols=None):
        # default to the initialized values, which default to hardcoded values if nothing was ever set
        prime_text = prime_text or self.prime_text
        num_sample_symbols = num_sample_symbols or self.num_sample_symbols

        if not self.sess or not self.checkpoint:
            print('ERROR! Failed to initialize Tensorflow session!')
            return 'ERROR! Failed to initialize Tensorflow session!', True
        else:
            return self.model.sample(self.sess, self.chars, self.vocab, num_sample_symbols, prime_text, self.sample_style), False

if __name__ == '__main__':
    x = Sampler()
    print(x.sample())
