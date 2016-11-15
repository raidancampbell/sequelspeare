import codecs
import os
import collections
from six.moves import cPickle
import numpy as np


class TextLoader:
    def __init__(self, data_dir, batch_size, seq_length):
        self.data_dir = data_dir
        self.batch_size = batch_size
        self.seq_length = seq_length
        # initialize variables, to prevent
        self.pointer = 0
        self.chars = []
        self.vocab_size = 0
        self.vocab = {}
        self.tensor = []
        self.num_batches = 0
        self.x_batches = 0
        self.y_batches = 0

        input_file = os.path.join(data_dir, "input.log")
        vocab_file = os.path.join(data_dir, "vocab.pkl")
        tensor_file = os.path.join(data_dir, "data.npy")

        print("preprocessing text file...")
        self.preprocess_char(input_file, vocab_file, tensor_file)
        print("preprocessed text file.")
        self.create_batches()

    def preprocess_char(self, input_file, vocab_file, tensor_file):
        with codecs.open(input_file, "r", encoding='utf-8') as f:
            data = f.read()
            counter = collections.Counter(data)
            count_pairs = sorted(counter.items(), key=lambda x: -x[1])
            self.chars, _ = zip(*count_pairs)
            self.vocab_size = len(self.chars)
            self.vocab = dict(zip(self.chars, range(len(self.chars))))
            with open(vocab_file, 'wb') as vocab_file_opened:
                cPickle.dump(self.chars, vocab_file_opened)
            self.tensor = np.array(list(map(self.vocab.get, data)))
            np.save(tensor_file, self.tensor)

    def preprocess_word(self, input_file, vocab_file, tensor_file):
        with codecs.open(input_file, "r", encoding='utf-8') as f:
            data = f.read()
            counter = collections.Counter(data.split())
            count_pairs = sorted(counter.items(), key=lambda x: -x[1])
            self.chars, _ = zip(*count_pairs)
            self.vocab_size = len(self.chars)
            self.vocab = dict(zip(self.chars, range(len(self.chars))))
            with open(vocab_file, 'wb') as vocab_file_opened:
                cPickle.dump(self.chars, vocab_file_opened)
            self.tensor = np.array(list(map(self.vocab.get, data)))
            np.save(tensor_file, self.tensor)

    def create_batches(self):
        self.num_batches = int(self.tensor.size / (self.batch_size * self.seq_length))

        self.tensor = self.tensor[:self.num_batches * self.batch_size * self.seq_length]
        x_data = self.tensor
        y_data = np.copy(self.tensor)
        y_data[:-1] = x_data[1:]
        y_data[-1] = x_data[0]
        self.x_batches = np.split(x_data.reshape(self.batch_size, -1), self.num_batches, 1)
        self.y_batches = np.split(y_data.reshape(self.batch_size, -1), self.num_batches, 1)

    def next_batch(self):
        x, y = self.x_batches[self.pointer], self.y_batches[self.pointer]
        self.pointer += 1
        return x, y

    def reset_batch_pointer(self):
        self.pointer = 0
