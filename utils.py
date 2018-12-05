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
        # initialize variables, to prevent the linter from complaining
        self.pointer = 0
        self.chars = []
        self.vocab_size = 0
        self.vocab = {}
        self.tensor = []
        self.num_batches = 0
        self.x_batches = []
        self.y_batches = []

        input_file = os.path.join(data_dir, "input.log")
        vocab_file = os.path.join(data_dir, "vocab.pkl")
        tensor_file = os.path.join(data_dir, "data.npy")

        print("preprocessing text file...")
        self.preprocess(input_file, vocab_file, tensor_file, remove_timestamps=True, tokenize_by_word=False)
        print("preprocessed text file.")
        self.create_batches()

    # removes the timestamp from the beginning of each line in the string
    # optionally, it also removes the username
    @staticmethod
    def _remove_timestamps(string, remove_username=False):
        result = ''
        for line in string.split('\n'):
            result += ' '.join(line.split()[2 if remove_username else 1:]) + '\n'
        return result

    # preprocesses the data into lookup dicts of char-to-int
    # optionally (on by default) strips the timestamps from the beginning of each line in the dataset
    # optionally (off by default) tokenizes the string by words instead of characters
    def preprocess(self, input_file, vocab_file, tensor_file, remove_timestamps=True, tokenize_by_word=False):
        with codecs.open(input_file, "r", encoding='utf-8') as f:
            data = TextLoader._remove_timestamps(f.read()) if remove_timestamps else f.read()
            counter = collections.Counter(data.split() if tokenize_by_word else data)
            count_pairs = sorted(counter.items(), key=lambda x: -x[1])
            self.chars, _ = zip(*count_pairs)  # list of tokens ever used
            self.vocab_size = len(self.chars)  # number of unique tokens
            self.vocab = dict(zip(self.chars, range(len(self.chars))))  # lookup conversion from unique token ID to token
            with open(vocab_file, 'wb') as vocab_file_opened:
                cPickle.dump(self.chars, vocab_file_opened)
            self.tensor = np.array(list(map(self.vocab.get, data)))  # create a tensor representation of the data using token IDs
            np.save(tensor_file, self.tensor)  # save the tensor

    # batch the data up into premade chunks.  The dataset is quite large
    def create_batches(self):
        # there are len(tensor)/(batch_size*seq_length) many batches.  Note the integer truncation.
        self.num_batches = int(self.tensor.size / (self.batch_size * self.seq_length))
        # tensor is a rank-1 tensor evenly divisible into batches, with remaining data having been truncated
        self.tensor = self.tensor[:self.num_batches * self.batch_size * self.seq_length]
        x_data = self.tensor
        y_data = np.copy(self.tensor)  # do a deep copy.  Alternatively you could use a gnarly indexing algorithm
        y_data[:-1] = x_data[1:]  # y_data, the target data, is simply the next value of x_data, the source data
        y_data[-1] = x_data[0]  # the last element of target data is wrapped to be the first element of the source
        # Trimming instead of repeating imbalance the batching.  similarly, the dataset is massive and this is a single hiccup.
        self.x_batches = np.split(x_data.reshape(self.batch_size, -1), self.num_batches, 1)  # split the data into batches
        self.y_batches = np.split(y_data.reshape(self.batch_size, -1), self.num_batches, 1)  # again, the only difference is off-by-one

    # grab the next batch of data, iterating an internal pointer to the current batch
    def next_batch(self):
        x, y = self.x_batches[self.pointer], self.y_batches[self.pointer]
        self.pointer += 1
        return x, y

    # reset the internal batch pointer, effectively resetting the referenced batches to the first one
    def reset_batch_pointer(self):
        self.pointer = 0
