import os
import pytest
from datetime import datetime
from ..json_storage import MyJsonStorageHandler

JSON_BASE = os.path.join(os.path.dirname(__file__), 'json_dbs')

@pytest.fixture(scope="module", autouse=True)
def my_fixture():
    pass

def get_storage():
    storage = MyJsonStorageHandler()
    storage.set_paths(JSON_BASE, str(datetime.now().utcnow()))
    return storage

CREATE_RECORD = {
        "create": {
            "a": {
                "path": "records",
                "record": {
                    "name": "tim",
                    "age": 23
                }
            }
        }
    }
READ_RECORDS = {
        "read": {
            "records": {"path":"records"}
        }
    }

def test_create():
    storage = get_storage()
    result = storage.do_actions(0, CREATE_RECORD)
    new_id = result['new_ids']["a"]
    result = storage.do_actions(result['revision'], READ_RECORDS)
    assert len(result["queries"]["records"]) == 1
    record = result["queries"]["records"][0]
    assert record["id"] == new_id
    assert record["name"] == "tim"


def test_transaction_commit():
    storage = get_storage()
    transaction_id = storage.start_transaction()['transaction_id']
    result = storage.do_actions(0, CREATE_RECORD, transaction_id)
    storage.commit_transaction(transaction_id)
    result = storage.do_actions(result['revision'], READ_RECORDS)
    assert len(result["queries"]["records"]) == 1


def test_transaction_abort():
    pass


def test_transaction_timeout():
    pass

def test_error_transaction_timed_out():
    pass


def test_error_transaction_in_progress():
    pass


def test_transaction_error_no_transaction_in_progress():
    pass


def test_error_transaction_id_mismatcht():
    pass

