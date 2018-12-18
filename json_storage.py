"""
A crude but flexible

per user JSON database which takes modification instructions as json.


We track the , which the client can use to determine if its data is dirty.



"""
import os
import datetime
import ujson


class ApiError(Exception):

    def __init__(self, code="uncaught", msg="", data=None):
        super(Exception, self).__init__('{} -- {}'.format(code, msg))
        self.code = code
        self.data = data


class JsonTwoFileStorageHandler():
    """
    Transaction aware json database. Allows only one transaction.

    Methods for working with two-file system:
        xyz_data_db.json  --  the data object which is entirely modifiable by clients
        xyz_meta_db.json  --  meta data such as the last_id and revision.


    """
    def __init__(self):
        self._must_reload = True
        self.transaction_id = None
        self.transaction_initiated = None
        self.transaction_timeout = None
        self.data_db = None
        self.meta_db = None
        self._data_db_path = None
        self._meta_db_path = None

    def set_paths(self, base_path, database_name):
        self._data_db_path = self._get_db_path(base_path, database_name, 'data_db')
        self._meta_db_path = self._get_db_path(base_path, database_name, 'meta_db')

    def load(self):
        if self.transaction_id is not None:
            now = datetime.datetime.now()
            timeout = self.transaction_initiated + datetime.timedelta(seconds=self.transaction_timeout)
            if timeout > now:
                self._must_reload = True

        if self._must_reload:
            self.data_db = self._load_json(self._data_db_path)
            self.meta_db = self._load_json(self._meta_db_path)
            if self.meta_db == {}:
                self.meta_db = {'rev': 0, 'last_id': 0}
            self._must_reload = False

    def save(self):
        self._save_json(self._data_db_path, self.data_db)
        self._save_json(self._meta_db_path, self.meta_db)

    def start_transaction(self, timeout=5):
        transaction_id = 100
        self.transaction_id = transaction_id
        self.transaction_initiated = datetime.datetime.now()
        self.transaction_timeout = timeout
        return transaction_id

    def commit_transaction(self, transaction_id):
        if transaction_id == self.transaction_id:
            self.save()
        self.transaction_id = None

    def abort_transaction(self, transaction_id):
        if transaction_id == self.transaction_id:
            self._must_reload = True
        self.transaction_id = None

    def check_transaction(self, transaction_id):
        if transaction_id is None and self.transaction_id is None:
            # No transaction expected or in progress, all good
            return
        if transaction_id is None and self.transaction_id is not None:
            raise ApiError(code='transaction_in_progress')
        if transaction_id is not None and self.transaction_id is None:
            raise ApiError(code='no_transaction_in_progress')
        if transaction_id != self.transaction_id:
            raise ApiError(code='transaction_id_mismatch')

    def check_revision(self, revision):
        if int(revision) != self.meta_db['rev']:
            raise ApiError(code='revision_mismatch', data={
                'client_revision': int(revision),
                'server_revision': self.meta_db['rev'],
                })

    def _save_json(self, filepath, data):
        with open(filepath, 'w') as fp:
            ujson.dump(data, fp, indent=4)

    def _load_json(self, filepath):
        if not os.path.exists(filepath):
            self._save_json(filepath, {})
        with open(filepath) as fp:
            return ujson.load(fp)

    def _get_db_path(self, base_path, database_name, suffix):
        return os.path.join(base_path, '{}_{}.json'.format(database_name, suffix))


class ActionsMixin():
    valid_actions = ('create', 'read', 'update', 'delete')

    def do_actions(self, revision, action_sets, transaction_id=None):
        """
        @revision: the client stored revision
        @action_sets: changes to make
        @transaction_id: the id of the pending transaction if there is one
        """
        self.load()
        self.check_transaction(transaction_id)
        self.check_revision(revision)
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
        if transaction_id is None:
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