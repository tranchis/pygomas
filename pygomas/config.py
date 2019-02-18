import os

DEFAULT_DATA_PATH = ".{sep}maps{sep}".format(sep=os.sep)


class Config(object):
    def __init__(self):
        self.data_path = DEFAULT_DATA_PATH

    def set_data_path(self, data_path):
        self.data_path = data_path + os.sep
