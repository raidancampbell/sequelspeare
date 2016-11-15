import tensorflow as tf
import time
import os
from sequelspeare.model import Model
from sequelspeare.utils import TextLoader
from six.moves import cPickle

EPOCHS = 10
LEARNING_RATE = 0.05
DECAY_RATE = 0.9
SAVE_DIR = 'savedata'
SAVE_FREQ = 500

data_loader = TextLoader('.', Model.BATCH_SIZE, Model.SEQUENCE_LENGTH)
model = Model(data_loader.vocab_size)

with open(os.path.join(SAVE_DIR, 'chars_vocab.pkl'), 'wb') as f:
    cPickle.dump((data_loader.chars, data_loader.vocab), f)

# with tf.device("/gpu:0"):
with tf.Session() as sess:
    tf.initialize_all_variables().run()
    for epoch in range(EPOCHS):
        sess.run(tf.assign(model.lr, LEARNING_RATE * (DECAY_RATE ** epoch)))
        data_loader.reset_batch_pointer()
        state = sess.run(model.initial_state)
        for b in range(data_loader.num_batches):
            start = time.time()
            x, y = data_loader.next_batch()
            feed = {model.input_data: x, model.targets: y}
            for i, (c, h) in enumerate(model.initial_state):
                feed[c] = state[i].c
                feed[h] = state[i].h

            train_loss, state, _ = sess.run([model.cost, model.final_state, model.train_op], feed)
            end = time.time()
            print("{}/{} (epoch {}), train_loss = {:.3f}, time/batch = {:.3f}".format(epoch * data_loader.num_batches + b,
                                                                                      EPOCHS * data_loader.num_batches,
                                                                                      epoch, train_loss, end - start))

            # save for the last result
            if (epoch * data_loader.num_batches + b) % SAVE_FREQ == 0 or (epoch == EPOCHS - 1 and b == data_loader.num_batches - 1):
                checkpoint_path = os.path.join(SAVE_DIR, 'model.ckpt')
                tf.train.Saver(tf.all_variables()).save(sess, checkpoint_path, global_step=epoch * data_loader.num_batches + b)
                print("model saved to {}".format(checkpoint_path))
