import tensorflow as tf
import time
import os
from sequelspeare.model import Model
from sequelspeare.utils import TextLoader
from six.moves import cPickle
import csv

# hyperparameters that shouldn't really be dynamically adjusted
EPOCHS = 3  # this should be longer for actual training. Like 30.
LEARNING_RATE = 0.002
DECAY_RATE = 0.95
SAVE_DIR = 'savedata'
SAVE_FREQ = 1000

# load the data, and save the symbol tables
data_loader = TextLoader('.', Model.BATCH_SIZE, Model.SEQUENCE_LENGTH)
model = Model(data_loader.vocab_size)
with open(os.path.join(SAVE_DIR, 'chars_vocab.pkl'), 'wb') as f:
    cPickle.dump((data_loader.chars, data_loader.vocab), f)

# housekeeping on training metadata to draw graphs and statistics
filename = 'training_' + str(model.LAYER_WIDTH) + 'x' + str(model.NUM_LAYERS) + '_' + \
           str(LEARNING_RATE) + 'l_'+str(DECAY_RATE) + 'd_' + str(EPOCHS) + 'e.csv'  # well-defined standard for naming the metadata
out_file = open(filename, 'w')
csv_writer = csv.writer(out_file)
csv_writer.writerow(['loss', 'time_taken'])
losses = []
times = []

# polite GPU memory allocation: don't grab everything you can.
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
config.gpu_options.allocator_type = 'BFC'
# learning happens here
with tf.Session(config=config) as sess:
    tf.initialize_all_variables().run()
    for epoch in range(EPOCHS):
        # tell the model its properly decayed learning rate
        sess.run(tf.assign(model.learning_rate, LEARNING_RATE * (DECAY_RATE ** epoch)))
        data_loader.reset_batch_pointer()  # begin at batch 0
        state = sess.run(model.initial_state)  # initialize the model
        for b in range(data_loader.num_batches):
            start = time.time()
            x, y = data_loader.next_batch()  # get the next source and target data batches
            feed = {model.input_data: x, model.targets: y}
            for layer_num, (c, h) in enumerate(model.initial_state):  # fill the feed dict with the data each tensor should apply
                feed[c] = state[layer_num].c  # tensor c should use tensor value state[layer_num].c
                feed[h] = state[layer_num].h  # from https://arxiv.org/pdf/1409.2329v5.pdf: c is the input, h is the memory
            # train the model
            train_loss, state, _ = sess.run([model.cost, model.final_state, model.train_op], feed)
            end = time.time()
            losses.append(train_loss)
            times.append(end - start)
            print("{}/{} (epoch {}), train_loss = {:.3f}, time/batch = {:.3f}".format(epoch * data_loader.num_batches + b,
                                                                                      EPOCHS * data_loader.num_batches,
                                                                                      epoch, train_loss, end - start))

            # save for the last result
            if (epoch * data_loader.num_batches + b) % SAVE_FREQ == 0 or (epoch == EPOCHS - 1 and b == data_loader.num_batches - 1):
                checkpoint_path = os.path.join(SAVE_DIR, 'model.ckpt')
                tf.train.Saver(tf.all_variables()).save(sess, checkpoint_path, global_step=epoch * data_loader.num_batches + b)
                print("saved to {}".format(checkpoint_path))
                if csv_writer:
                    for time_, loss_ in zip(times, losses):
                        csv_writer.writerow([loss_, time_])
                    losses.clear()
                    times.clear()

out_file.close()
