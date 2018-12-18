"""
A crude but flexible

per user JSON database which takes modification instructions as json.


We track the , which the client can use to determine if its data is dirty.



"""
import os
import ujson


class JsonTwoFileStorageHandler():
    """
    Methods for working with two-file system:
        xyz_data_db.json  --  the data object which is entirely modifiable by clients
        xyz_meta_db.json  --  meta data such as the last_id and revision.


    """

    def set_paths(self, base_path, database_name):
        self.database_name = database_name
        self.base_path = base_path
        self.data_db_path = self._get_db_path(database_name, 'data_db')
        self.meta_db_path = self._get_db_path(database_name, 'meta_db')

    def _save_json(self, filepath, data):
        with open(filepath, 'w') as fp:
            ujson.dump(data, fp, indent=4)

    def _load_json(self, filepath):
        if not os.path.exists(filepath):
            self._save_json(filepath, {})
        with open(filepath) as fp:
            return ujson.load(fp)

    def _get_db_path(self, database_name, suffix):
        return os.path.join(self.base_path, '{}_{}.json'.format(database_name, suffix))

    def load(self):
        self.data_db = self._load_json(self.data_db_path)
        self.meta_db = self._load_json(self.meta_db_path)
        if self.meta_db == {}:
            self.meta_db = {'rev': 0, 'last_id': 0}

    def save(self):
        self._save_json(self.data_db_path, self.data_db)
        self._save_json(self.meta_db_path, self.meta_db)


class ApiError(Exception):

    def __init__(self, code="uncaught", msg="", data=None):
        super(Exception, self).__init__('{} -- {}'.format(code, msg))
        self.code = code
        self.data = data


class ActionsMixin():
    valid_actions = ('create', 'read', 'update', 'delete')

    def do_actions(self, revision, action_sets):
        """
        Pass action_sets which define what changes to make.
        """
        self.load()
        if int(revision) != self.meta_db['rev']:
            raise ApiError(code='revision_mismatch', data={
                'client_revision': int(revision),
                'server_revision': self.meta_db['rev'],
                })
        result = {}
        for action_type, actions in action_sets.items():
            if action_type not in self.valid_actions:
                raise ApiError(code='invalid_action_type', data={
                    'action_type': action_type,
                    })
            action_results = {}
            for key, params in actions.items():
                action_results[key] = getattr(self, '_' + action_type)(**params)
            result[action_type] = action_results
        result['revision'] = self.meta_db['rev']
        self.save()
        return result

    def _drill(self, path):
        collection = self.data_db
        for chunk in path.split('/'):
            if chunk not in collection:
                collection[chunk] = {}
            collection = collection[chunk]
        return collection

    def _create(self, path, record):
        collection = self._drill(path)
        key = int(self.meta_db['last_id']) + 1
        record['id'] = key
        collection[key] = record
        self.meta_db['last_id'] = key
        self.meta_db['rev'] += 1
        return key

    def _update(self, path, key, record):
        """
        Update a record.
        """
        collection = self._drill(path)
        collection[key] = record
        record['id'] = key
        self.meta_db['rev'] += 1
        return key

    def _delete(self, path, key):
        """
        Delete a record.
        """
        collection = self._drill(path)
        del collection[key]
        self.meta_db['rev'] += 1
        return key

    def _read(self, path):
        """
        Reads a collection.
        TODO: allow filtering (but really, just structure it differently...)
        """
        collection = self._drill(path)
        return list(collection.values())


class MyJsonStorageHandler(ActionsMixin, JsonTwoFileStorageHandler):
    pass