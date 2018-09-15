from Features.AbstractFeature import AbstractFeature
import datetime
from escpos import *


class Printable(AbstractFeature):
    # printer_dev really should be specified, the default value here isn't common enough
    def __init__(self, printer_dev):
        self.printer_dev = printer_dev
        # defer initialization until the first message is seen.
        # This prevents try/catch on initialization, even when this feature is disabled
        self.epson = None

    def message_filter(self, bot, source, target, message, highlighted):
        if not self.epson:
            self.epson = self.epson or printer.Serial(self.printer_dev or '/dev/ttyUSB0')
            self.epson.set(align='left', font='b', width=1, height=1, density=9)
        timestamp = datetime.datetime.now()
        text = '{} {}: {}\n'.format(timestamp.strftime('%m/%d %H:%M:%S '), target, message)
        text = text.replace('\\', '\\\\')
        self.epson.text(text)
        return False
