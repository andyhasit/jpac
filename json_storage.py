"""
A crude but flexible JSON database which:
    - Acccepts modification instructions as json
    - Allows cross request transactions
    - Enables version mismatch handling

"""
import datetime
import uuid
from pointy.utils import JsonFileWrapper
from pointy.utils import ApiError

REV_KEY = 'rev'
LAST_ID_KEY = 'last_id'

class JsonTwoFileStorageHandler:
    """
    Transaction aware json database. Allows only one transaction.

    Methods for working with two-file system:
        xyz_data.json  --  the data object which is entirely modifiable by clients
        xyz_metadata.json  --  meta data such as the last_id and revision.


    """
    def __init__(self, data_db_path, metadata_db_path):
        self.data = None
        self._metadata = None
        self._must_reload = True
        self._transaction_id = None
        self._revision_before_transaction = None
        self._transaction_start_time = None
        self._transaction_timeout = None
        self._data_file_wrapper = JsonFileWrapper(data_db_path)
        self._meta_file_wrapper = JsonFileWrapper(metadata_db_path, {REV_KEY: 0, LAST_ID_KEY: 0})

    @property
    def revision(self):
        if self._metadata:
            return self._metadata[REV_KEY]

    @revision.setter
    def revision(self, value):
        self._metadata[REV_KEY] = value

    @property
    def last_id(self):
        if self._metadata:
            return self._metadata[LAST_ID_KEY]

    @last_id.setter
    def last_id(self, value):
        self._metadata[LAST_ID_KEY] = value

    def load(self):
        self._check_if_transaction_timed_out()
        if self._must_reload:
            self.data = self._data_file_wrapper.load(True)
            self._metadata = self._meta_file_wrapper.load(True)
            self._must_reload = False

    def save(self):
        self._data_file_wrapper.save()
        self._meta_file_wrapper.save()

    def start_transaction(self, timeout=5):
        self.load()
        self._revision_before_transaction = self.revision
        self._transaction_id = uuid.uuid4()
        self._transaction_start_time = datetime.datetime.now()
        self._transaction_timeout = timeout
        return {'transaction_id': self._transaction_id, 'revision': self.revision}

    def abort_transaction(self, transaction_id):
        """
        Still returns revision if transaction doesn't exist or timed out.
        """
        self.load()
        if transaction_id == self._transaction_id:
            self._rollback_transaction()
        return {'revision': self.revision}

    def commit_transaction(self, transaction_id):
        self.load()
        self.check_transaction(transaction_id)
        self.save()
        self._clear_transaction()
        return {'revision': self.revision}

    def check_transaction(self, transaction_id):
        if transaction_id is None and self._transaction_id is None:
            # No transaction expected or in progress, all good
            return
        if transaction_id is None and self._transaction_id is not None:
            raise ApiError(code='transaction_in_progress')
        if transaction_id is not None and self._transaction_id is None:
            raise ApiError(code='no_transaction_in_progress')
        if transaction_id != self._transaction_id:
            raise ApiError(code='transaction_id_mismatch')

    def check_revision(self, revision):
        if int(revision) != self.revision:
            raise ApiError(
                code='revision_mismatch',
                data={
                    'client_revision': revision,
                    'server_revision': self.revision,
                },
                msg='Client revision: {}. Server revision: {}'.format(revision, self.revision)
            )

    def _check_if_transaction_timed_out(self):
        if self._transaction_id is not None:
            now = datetime.datetime.now()
            timeout = self._transaction_start_time + datetime.timedelta(seconds=self._transaction_timeout)
            if now > timeout:
                self._rollback_transaction()
                raise ApiError(code='transaction_timed_out')

    def _clear_transaction(self):
        """
        To be called once a transaction is finished, regardless of outcome.
        """
        self._transaction_id = None
        self._revision_before_transaction = None

    def _rollback_transaction(self):
        """
        Annuls the current transaction.
        """
        assert self._transaction_id is not None
        self._must_reload = True
        self.revision = self._revision_before_transaction
        self._clear_transaction()


class ActionsMixin():
    """
    A mixin with the actions
    """
    def push_actions(self, revision, action_sets, transaction_id=None):
        """
        @revision: the client stored revision (we will check if it matches)
        @transaction_id: the id of the open transaction (optional)
        @action_sets: changes to make.

        The action_sets dict may contain keys:
            create > dict
            read   > dict
            update > list
            delete > list

        action_sets_example = {
            "create": {...},          # optional
            "read":   {...},          # optional
            "update": [...],          # optional
            "delete": [...],          # optional
        }

        The format for each is convered below

        The return dict will contains keys: revision, queries and new_ids

        result_example = {
            "revision": 1234,
            "queries":  {...},
            "new_ids":  {...}
        }

        Reads are performed last, so will take into account changes made

        read_example: {
            "query_a": {                    # the return identifier
                "path": "some/collection",  # the json path
                "as_list": true             # whether to convert to list
            },
            "query_b": {                    # the return identifier
                "path": "setting/13425",    # the json path
            }
        }
        result_example: {
            "revision": 1234,
            "new_ids": {...},
            "queries": {
                "query_a": [...],
                "query_b": {...}
            }
        }
        The key is used to match the query results in the resuts>read dict


        create_example: {
            "1": {                          # to match the new id in results
                "path": "some/collection",  # the json path
                "record": {                 # the record
                    "name": "tim",
                    "age": 23
                }
            }
        }
        result_example: {
            "revision": 1234,
            "queries": {...},
            "new_ids": {
                "1": 1234
            }
        }

        update_example: [                   # note this is a list
            {
                "key": "1234"               # the key of the object to edit
                "path": "some/collection",  # the json path
                "record": {                 # the record
                    "name": "tim",
                    "age": 23
                }
            }
        ]

        delete_example: [                   # note this is a list
            {
                "key": "1234"               # the key of the object to edit
                "path": "some/collection",  # the json path
            }
        ]


        """
        self.load()
        self.check_transaction(transaction_id)
        self.check_revision(revision)
        new_ids = {}
        queries = {}
        if 'create' in action_sets:
            for key, params in action_sets['create'].items():
                new_ids[key] = self._create(**params)
        if 'update' in action_sets:
            for params in action_sets['update']:
                self._update(**params)
        if 'delete' in action_sets:
            for params in action_sets['delete']:
                self._delete(**params)
        if 'read' in action_sets:
            for key, params in action_sets['read'].items():
                queries[key] = self._read(**params)
        result = {
            'revision': self.revision,
            'queries': queries,
            'new_ids': new_ids
        }
        if transaction_id is None:
            self.save()
        return result

    def _drill(self, path):
        collection = self.data
        for chunk in path.split('/'):
            if chunk != '':
                if chunk not in collection:
                    collection[chunk] = {}
                collection = collection[chunk]
        return collection

    def _create(self, path, record):
        collection = self._drill(path)
        new_id = self.last_id
        record['id'] = new_id
        collection[new_id] = record
        self.last_id = new_id
        self.revision += 1
        return new_id

    def _update(self, path, key, record):
        """
        Update a record.
        """
        collection = self._drill(path)
        collection[key] = record
        record['id'] = key
        self.revision += 1

    def _delete(self, path, key):
        """
        Delete a record.
        """
        collection = self._drill(path)
        del collection[key]
        self.revision += 1

    def _read(self, path):
        """
        Reads a collection.
        TODO: allow filtering (but really, just structure it differently...)
        """
        collection = self._drill(path)
        return list(collection.values())


class MyJsonStorageHandler(ActionsMixin, JsonTwoFileStorageHandler):
    pass