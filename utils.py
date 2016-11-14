import collections


# builds a dictionary of word to unique word ID
def build_vocab_words(string):
    data = string.split()
    counter = collections.Counter(data)
    count_pairs = sorted(counter.items(), key=lambda x: (-x[1], x[0]))

    words, _ = list(zip(*count_pairs))
    word_to_id = dict(zip(words, range(len(words))))

    return word_to_id


# builds a dictionary of word to unique word ID
def build_vocab_chars(string):
    data = list(string)
    counter = collections.Counter(data)
    count_pairs = sorted(counter.items(), key=lambda x: (-x[1], x[0]))

    words, _ = list(zip(*count_pairs))
    char_to_id = dict(zip(words, range(len(words))))

    return char_to_id


# segments the data into training, and validation datasets, following the 95%-5% rule
def segment_data(data_filename):
    with open(data_filename, 'r') as datafile:
        for i, l in enumerate(datafile, 1):        # i is the number of lines
            pass
        file_text = datafile.read()
        with open('training_data', 'w') as training_file:
            with open('validation_data', 'w') as validation_file:
                iterator = 0
                for line in file_text.split('\n'):
                    if i / iterator <= 0.95:
                        training_file.write(line + '\n')
                    else:
                        validation_file.write(line + '\n')

