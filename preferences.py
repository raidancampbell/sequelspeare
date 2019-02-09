import json
import os


class Preferences:
    def __init__(self, filename):
        self.contents = {}
        self.file_name = filename
        self.file_handle = None
        try:
            self.file_handle = open(self.file_name, 'rw')
        except FileNotFoundError:
            self.file_handle = open(self.file_name, 'rw+')
            self.contents = Preferences._generate_default_values()
            self._dump_and_flush()

    def read_value(self, key):
        return self.read_with_default(key)

    def read_with_default(self, key, default=None):
        if key in self.contents:
            return self.contents[key]
        elif key in self.contents['optional']:
            return self.contents['optional'][key]
        else:
            return default

    def write_value(self, key, value):
        if key in self.contents:
            self.contents[key] = value
        elif key in self.contents['optional']:
            self.contents['optional'][key] = value
        else:
            print(f'WARN! key "{key}" not found in preferences file, adding under optional...')
            self.contents['optional'][key] = value
        self._dump_and_flush()

    def _load_contents(self):
        self.contents = json.load(self.file_handle)

    def _dump_and_flush(self):
        json.dump(self.contents, self.file_handle, indent=2, sort_keys=True)
        os.fsync(self.file_handle.fileno())

    @staticmethod
    def _generate_default_values():
        default_contents = {'botnick': 'swiggityspeare', 'botownernick': 'foo', 'botrealname': 'a brainless bot',
                            'channels': ['#cwru'], 'reminders': [], 'serveraddress': 'irc.case.edu',
                            'serverport': '6667', 'whitelistnicks': [], 'optional': []}
        return default_contents

