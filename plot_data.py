import matplotlib.pyplot as plt
import numpy as np
import csv
import glob
import statistics


class Plotter:
    def __init__(self, should_plot=True):
        self.analyze(should_plot)

    @staticmethod
    def moving_average(a, n=3):
        ret = np.cumsum(a, dtype=float)
        ret[n:] = ret[n:] - ret[:-n]
        return ret[n - 1:] / n

    @staticmethod
    def analyze(should_plot, visibly_plot=False):
        filenames = glob.glob("training_metadata/training_*.csv")
        total_time = 0.
        with open('training_metadata/metadata_sum.csv', 'w') as summary_csv:
            summary_writer = csv.writer(summary_csv)
            for filenum, filename in enumerate(filenames):
                with open(filename, 'r') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    errors = []
                    trial_time = 0
                    for i, row in enumerate(reader):
                        if not i:
                            continue  # first row contains the header string
                        errors.append(float(row[0]))
                        total_time += float(row[1])
                        trial_time += float(row[1])
                    if not should_plot:
                        continue
                    if errors:
                        summary_writer.writerow([filename[27:-4], statistics.mean(errors[-2500:]), trial_time])
                        for i, substr_ in enumerate(filename[:-4].split('_')):
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
                        if visibly_plot:
                            plt.figure(filenum+1)
                        plt.plot(Plotter.moving_average(errors, n=2500))
                        title = width + ' by ' + depth + ' network. \n''\
                            learning rate: ' + learning_rate + ' decay rate: ' + decay_rate + ' epochs: ' + epochs
                        plt.title(title)
                        plt.savefig(filename[:-4] + '.png')
                        print('[' + str(filenum) + '/' + str(len(filenames)) + '] Finished analyzing file: ' + filename)
                        # if we're not viewing the interactive figures, clear the figure to free up memory
                        if not visibly_plot:
                            plt.clf()
            if visibly_plot:
                plt.show()
            print('total training time: ' + str(total_time) + ' seconds')


if __name__ == '__main__':
    Plotter()
