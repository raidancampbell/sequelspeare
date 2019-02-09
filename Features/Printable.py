from Features.AbstractFeature import AbstractFeature
import datetime
from escpos import *


class Printable(AbstractFeature):
    @staticmethod
    def description():
        return 'Passively prints all messages the bot sees to an epson thermal printer.'

    # printer_dev really should be specified, the default value here isn't common enough
    def __init__(self, printer_dev):
        self.printer_dev = printer_dev
        # defer initialization until the first message is seen.
        # This prevents try/catch on initialization, even when this feature is disabled
        self.epson = None
        self.failed_initialization = False

    def message_filter(self, bot, source, target, message, highlighted):
        if self.failed_initialization:
            return False
        if not self.epson:
            try:
                self.epson = self.epson or printer.Serial(self.printer_dev or '/dev/ttyUSB0')
                self.epson.set(align='left', font='b', width=1, height=1, density=9)
            except Exception as e:
                print('failed to initialize printer, silently ignoring')
                print(e)
                self.failed_initialization = True
        timestamp = datetime.datetime.now()
        text = f'{timestamp.strftime("%m/%d %H:%M:%S ")} {target}: {message}\n'
        text = text.replace('\\', '\\\\')
        self.epson.text(text)
        return False
