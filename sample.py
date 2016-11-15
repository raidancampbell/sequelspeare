import tensorflow as tf
import os
from six.moves import cPickle
from sequelspeare.model import Model


# This object creates a TF session: you will run into issues if you instantiate it while training
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
            self.sess.as_default()
            tf.initialize_all_variables().run(session=self.sess)
            self.checkpoint = tf.train.get_checkpoint_state(self.save_dir)
            if self.checkpoint and self.checkpoint.model_checkpoint_path:
                tf.train.Saver(tf.all_variables()).restore(self.sess, self.checkpoint.model_checkpoint_path)

    def sample(self):
        if not self.sess or not self.checkpoint:
            print('ERROR! Failed to initialize Tensorflow session!')
            return 'ERROR! Failed to initialize Tensorflow session!'
        else:
            return self.model.sample(self.sess, self.chars, self.vocab, self.num_sample_symbols, self.prime_text, self.sample_style)

if __name__ == '__main__':
    x = Sampler()
    print(x.sample())