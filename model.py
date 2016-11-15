import tensorflow as tf
import numpy as np
from tensorflow.python.ops import rnn_cell
from tensorflow.python.ops import seq2seq


class Model:
    LAYER_WIDTH = 64
    NUM_LAYERS = 2
    BATCH_SIZE = 100
    SEQUENCE_LENGTH = 50
    GRADIENT_CLIP = 5.0
    PRIME = 'the '

    def __init__(self, vocab_size, is_sampled=False):
        cell_fn = rnn_cell.BasicLSTMCell
        cell = cell_fn(self.LAYER_WIDTH, state_is_tuple=True)
        self.cell = cell = rnn_cell.MultiRNNCell([cell] * self.NUM_LAYERS, state_is_tuple=True)
        self.vocab_size = vocab_size

        # these can theoretically be changed to int8
        self.input_data = tf.placeholder(tf.int32, [self.BATCH_SIZE, self.SEQUENCE_LENGTH])
        self.targets = tf.placeholder(tf.int32, [self.BATCH_SIZE, self.SEQUENCE_LENGTH])
        self.initial_state = cell.zero_state(self.BATCH_SIZE, tf.float32)

        with tf.variable_scope('rnnlm'):
            softmax_w = tf.get_variable("softmax_w", [self.LAYER_WIDTH, vocab_size])
            softmax_b = tf.get_variable("softmax_b", [vocab_size])
            with tf.device("/cpu:0"):
                embedding = tf.get_variable("embedding", [vocab_size, self.LAYER_WIDTH])
                inputs = tf.split(1, self.SEQUENCE_LENGTH, tf.nn.embedding_lookup(embedding, self.input_data))
                inputs = [tf.squeeze(input_, [1]) for input_ in inputs]

        def loop(prev, _):
            prev = tf.matmul(prev, softmax_w) + softmax_b
            prev_symbol = tf.stop_gradient(tf.argmax(prev, 1))
            return tf.nn.embedding_lookup(embedding, prev_symbol)

        outputs, last_state = seq2seq.rnn_decoder(inputs, self.initial_state, cell, loop_function=loop if is_sampled else None, scope='rnnlm')
        output = tf.reshape(tf.concat(1, outputs), [-1, self.LAYER_WIDTH])
        self.logits = tf.matmul(output, softmax_w) + softmax_b
        self.probs = tf.nn.softmax(self.logits)
        loss = seq2seq.sequence_loss_by_example([self.logits], [tf.reshape(self.targets, [-1])],
                                                [tf.ones([self.BATCH_SIZE * self.SEQUENCE_LENGTH])], vocab_size)
        self.cost = tf.reduce_sum(loss) / self.BATCH_SIZE / self.SEQUENCE_LENGTH
        self.final_state = last_state
        self.lr = tf.Variable(0.0, trainable=False)
        tvars = tf.trainable_variables()
        grads, _ = tf.clip_by_global_norm(tf.gradients(self.cost, tvars), self.GRADIENT_CLIP)
        optimizer = tf.train.AdamOptimizer(self.lr)
        self.train_op = optimizer.apply_gradients(zip(grads, tvars))

    def sample(self, sess, chars, vocab, num=200, prime=PRIME, sampling_type=1):
        state = sess.run(self.cell.zero_state(1, tf.float32))
        for char in prime[:-1]:
            x = np.zeros((1, 1))
            x[0, 0] = vocab[char]
            feed = {self.input_data: x, self.initial_state: state}
            [state] = sess.run([self.final_state], feed)

        def weighted_pick(weights):
            t = np.cumsum(weights)
            s = np.sum(weights)
            return int(np.searchsorted(t, np.random.rand(1) * s))

        ret = prime
        char = prime[-1]
        for n in range(num):
            x = np.zeros((1, 1))
            x[0, 0] = vocab[char]
            feed = {self.input_data: x, self.initial_state: state}
            [probs, state] = sess.run([self.probs, self.final_state], feed)
            p = probs[0]

            if sampling_type == 0:
                sample = np.argmax(p)
            elif sampling_type == 2:
                if char == ' ':
                    sample = weighted_pick(p)
                else:
                    sample = np.argmax(p)
            else:  # sampling_type == 1 default:
                sample = weighted_pick(p)

            pred = chars[sample]
            ret += pred
            char = pred
        return ret
