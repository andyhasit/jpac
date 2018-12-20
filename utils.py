import os
import ujson


class JsonFileWrapper:
    """Wrapper around a json file"""

    def __init__(self, filepath):
        self.filepath = filepath

    def save(self, data):
        with open(self.filepath, 'w') as fp:
            ujson.dump(data, fp, indent=4)

    def load(self):
        if not os.path.exists(self.filepath):
            self.save({})
        with open(self.filepath) as fp:
            return ujson.load(fp)


def get_two_file_paths(base_path, database_name):
    """
    Utility function which returns two file paths:
        /path/database_name_data_db.json
        /path/database_name_meta_db.json
    """
    def path(suffix):
        return os.path.join(base_path, '{}_{}.json'.format(database_name, suffix))
    return path('data_db'), path('meta_db')
