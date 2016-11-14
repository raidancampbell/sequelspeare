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
