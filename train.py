import tensorflow as tf
EPOCHS = 10
LEARNING_RATE = 0.05
DECAY_RATE = 0.9

with tf.Session() as sess:
    tf.initialize_all_variables().run()
    for epoch in range(EPOCHS):
        sess.run(tf.assign(model.lr, LEARNING_RATE * (DECAY_RATE ** epoch)))
