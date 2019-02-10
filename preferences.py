import json
import os
from json import JSONDecodeError


class Preferences:
    def __init__(self, filename):
        self.contents = {}
        self.file_name = filename
        file_handle = None
        try:
            file_handle = open(self.file_name, 'r+')
            self._load_contents(file_handle)
            file_handle.close()
        except FileNotFoundError:
            if file_handle and not file_handle.closed:
                file_handle.close()
            with open(self.file_name, 'a+') as _:
                pass  # just here to create the file.
            self.contents = Preferences._generate_default_values()
            self._dump_and_flush()
        except JSONDecodeError:
            print(f'Failed to parse JSON from {filename}!\nDelete file to recreate with defaults')
            exit(1)

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

    def _load_contents(self, file_handle):
        self.contents = json.load(file_handle)

    def _dump_and_flush(self):
        with open(self.file_name, 'w') as file_handle:
            json.dump(self.contents, file_handle, indent=2, sort_keys=True)

    @staticmethod
    def _generate_default_values():
        default_contents = {'botnick': 'swiggityspeare', 'botownernick': 'foo', 'botrealname': 'a brainless bot',
                            'channels': ['#cwru'], 'reminders': [], 'serveraddress': 'irc.case.edu',
                            'serverport': '6667', 'whitelistnicks': [], 'optional': []}
        return default_contents


prefs_singleton = Preferences('preferences.json')
