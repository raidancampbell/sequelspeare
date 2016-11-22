import tensorflow as tf
import numpy as np
from tensorflow.python.ops import rnn_cell
from tensorflow.python.ops import seq2seq


class Model:
    LAYER_WIDTH = 256
    NUM_LAYERS = 3
    BATCH_SIZE = 50
    SEQUENCE_LENGTH = 50
    GRADIENT_CLIP = 5.0
    PRIME = 'swiggityspeare '

    def __init__(self, vocab_size, is_sampled=False):
        self.cell = rnn_cell.MultiRNNCell([rnn_cell.BasicLSTMCell(self.LAYER_WIDTH, state_is_tuple=True)] * self.NUM_LAYERS, state_is_tuple=True)
        self.vocab_size = vocab_size

        if is_sampled:
            self.BATCH_SIZE = 1
            self.SEQUENCE_LENGTH = 1

        # these can theoretically be changed to int8 for character tokenization
        # the actual representation should be ceil(log_2(vocab_size))
        # preps the tensors for data to be added.
        self.input_data = tf.placeholder(tf.int32, [self.BATCH_SIZE, self.SEQUENCE_LENGTH])
        self.targets = tf.placeholder(tf.int32, [self.BATCH_SIZE, self.SEQUENCE_LENGTH])
        self.initial_state = self.cell.zero_state(self.BATCH_SIZE, tf.float32)

        # in the recurrent neural network language model namespace
        with tf.variable_scope('rnnlm'):
            softmax_w = tf.get_variable("softmax_w", [self.LAYER_WIDTH, vocab_size])
            softmax_b = tf.get_variable("softmax_b", [vocab_size])
            with tf.device("/cpu:0"):
                # grab the tensor-space embedding distribution of our data
                embedding = tf.get_variable("embedding", [vocab_size, self.LAYER_WIDTH])
                # split the embeddings into sequences along the first dimension
                inputs_ = tf.split(1, self.SEQUENCE_LENGTH, tf.nn.embedding_lookup(embedding, self.input_data))
                # lower the tensor ranking by removing the single-length dimension
                inputs = [tf.squeeze(input_, [1]) for input_ in inputs_]
                # `inputs` now contains an array of proper-length input data tensors

        def loop(prev, _):
            prev = tf.matmul(prev, softmax_w) + softmax_b
            prev_symbol = tf.stop_gradient(tf.argmax(prev, 1))
            return tf.nn.embedding_lookup(embedding, prev_symbol)

        # propagate the network.  If we're sampling instead of training, simulate with the `loop` function.
        outputs, last_state = seq2seq.rnn_decoder(inputs, self.initial_state, self.cell, loop_function=loop if is_sampled else None, scope='rnnlm')

        # concatenate along the first dimension, then shape the result such that it is the same width and depth as the network
        output = tf.reshape(tf.concat(1, outputs), [-1, self.LAYER_WIDTH])

        # generate the logits and then probability tensor for the outputs
        self.logits = tf.matmul(output, softmax_w) + softmax_b
        self.probs = tf.nn.softmax(self.logits)

        # calculate the loss using weighted cross-entropy
        loss = seq2seq.sequence_loss_by_example([self.logits], [tf.reshape(self.targets, [-1])],
                                                [tf.ones([self.BATCH_SIZE * self.SEQUENCE_LENGTH])], vocab_size)
        # from the loss, calculate a normalized cost vector
        self.cost = tf.reduce_sum(loss) / self.BATCH_SIZE / self.SEQUENCE_LENGTH
        self.final_state = last_state

        self.learning_rate = tf.Variable(0.0, trainable=False)  # don't optimize the hyperparameters of the optimizer.
        #  optimizer variables by default are considered trainable, and tried to be optimized.

        trainable_vars = tf.trainable_variables()
        # generate the gradients, clipped to a maximum value
        clipped_grads, _ = tf.clip_by_global_norm(tf.gradients(self.cost, trainable_vars), self.GRADIENT_CLIP)
        optimizer = tf.train.AdamOptimizer(self.learning_rate)

        # create the optimizer for use when training
        self.train_op = optimizer.apply_gradients(zip(clipped_grads, trainable_vars))

    # sample things from the trained network
    # the returned sample begins with the prime text, and `num` characters are appended to it
    # thus the length of the returned text is `len(prime) + num`
    def sample(self, sess, chars, vocab, num=140, prime=PRIME, sampling_type=1):
        state = sess.run(self.cell.zero_state(1, tf.float32))
        for token in prime[:-1]:
            x = np.zeros((1, 1))  # create a 1x1 array (single element, but two-dimensional)
            x[0, 0] = vocab[token]  # set the variable to the ID of the current character
            feed = {self.input_data: x, self.initial_state: state}
            [state] = sess.run([self.final_state], feed_dict=feed)

        # returns a randomly chosen index in the weight array, where the randomness is weighted by the weights
        def weighted_pick(weights):
            sum_array = np.cumsum(weights)  # create a cumulative sum array
            sum_vector = np.sum(weights)  # create a complete sum vector
            # return the index of the random pick, where the random pick is naturally weighted by the input weights
            return int(np.searchsorted(sum_array, np.random.rand(1) * sum_vector))

        total_response = prime
        token = prime[-1]
        for n in range(num):
            x = np.zeros((1, 1))
            x[0, 0] = vocab[token]
            feed = {self.input_data: x, self.initial_state: state}
            # query the network: given the current token and the previous ones, what's the probability distribution for the next tokens
            [probs, state] = sess.run([self.probs, self.final_state], feed)
            token_prob_dist = probs[0]  # vector of probability for the next character following the input character

            if sampling_type == 0:  # greedy.  Pick the most probable next character
                predicted_next_token_id = np.argmax(token_prob_dist)
            elif sampling_type == 2:  # greedy-in-word, weighted-random between words
                if token == ' ':
                    predicted_next_token_id = weighted_pick(token_prob_dist)
                else:
                    predicted_next_token_id = np.argmax(token_prob_dist)
            else:  # default: weighted random choice
                predicted_next_token_id = weighted_pick(token_prob_dist)

            predicted_next_token = chars[predicted_next_token_id]
            total_response += predicted_next_token
            token = predicted_next_token
        return total_response
