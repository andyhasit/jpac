import os
import ujson


class ApiError(Exception):

    def __init__(self, code="uncaught", msg=None, data=None):
        if msg is None:
            msg = code
        super(Exception, self).__init__(msg)
        self.code = code
        self.data = data


class JsonFileWrapper:
    """Wrapper around a json file"""

    def __init__(self, filepath, initial_data=None):
        if initial_data is None:
            initial_data = {}
        self._filepath = filepath
        self._must_reload = True
        self._loaded_timestamp = None
        self._data = initial_data

    def save(self, data=None):
        if data is None:
            data = self._data
        with open(self._filepath, 'w') as fp:
            ujson.dump(data, fp, indent=4)

    def load(self, force=False):
        if force or self._must_reload or self._file_on_disk_changed():
            if not os.path.exists(self._filepath):
                self.save()
            with open(self._filepath) as fp:
                self._data = ujson.load(fp)
            self._must_reload = False
        return self._data

    def _file_on_disk_changed(self):
        # TODO: implement
        return False
        if self._loaded_timestamp is None:
            return True


def get_two_file_paths(base_path, database_name):
    """
    Utility function which returns two file paths:
        /path/database_name_data_db.json
        /path/database_name_meta_db.json
    """
    def path(suffix):
        return os.path.join(base_path, '{}_{}.json'.format(database_name, suffix))
    return path('data_db'), path('meta_db')
