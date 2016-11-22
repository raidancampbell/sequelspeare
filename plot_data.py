import matplotlib.pyplot as plt
import numpy as np
import csv
import glob


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

for filenum, file in enumerate(glob.glob("*.csv")):
    with open(file) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        errors = []
        for i, row in enumerate(reader):
            if not i:
                continue
            errors.append(float(row[0]))
        if errors:
            for i, substr_ in enumerate(file[:-4].split('_')):
                if not i:
                    continue
                if 'x' in substr_:
                    width = substr_.split('x')[0]
                    depth = substr_.split('x')[1]
                if 'l' in substr_:
                    learning_rate = substr_[:-1]
                if 'd' in substr_:
                    decay_rate = substr_[:-1]
                if 'e' in substr_:
                    epochs = substr_[:-1]
            plt.figure(filenum+1)
            plt.plot(moving_average(errors, n=500))
            title = width + ' by ' + depth + ' network. \rlearning rate: ' + learning_rate + ' decay rate: ' + decay_rate + ' epochs: ' + epochs
            plt.title(title)
plt.show()
