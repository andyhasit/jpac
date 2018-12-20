import os
import pytest
from ..json_storage import MyJsonStorageHandler
from ..utils import ApiError
from .utils_for_tests import wipe_json_dbs, tmp_db_file


JSON_TEST_DIR = os.path.join(os.path.dirname(__file__), 'json_dbs')
'''
@pytest.fixture(scope="module", autouse=True)
def my_fixture():
    wipe_json_dbs()
'''

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


def get_storage():
    return MyJsonStorageHandler(tmp_db_file('data'), tmp_db_file('meta'))


def test_create():
    storage = get_storage()
    result = storage.push_actions(0, CREATE_RECORD)
    new_id = result['new_ids']["a"]
    result = storage.push_actions(result['revision'], READ_RECORDS)
    assert len(result["queries"]["records"]) == 1
    record = result["queries"]["records"][0]
    assert record["id"] == new_id
    assert record["name"] == "tim"


def test_update():
    storage = get_storage()
    result = storage.push_actions(0, CREATE_RECORD)
    original_revision = result['revision']
    new_id = result['new_ids']["a"]
    result = storage.push_actions(result['revision'], READ_RECORDS)
    result = storage.push_actions(result['revision'], {
        'update': [
            {
                "key": new_id,
                "path": "records",
                "record": {
                    "name": "andrea"
                }
            }
        ]
    })
    result = storage.push_actions(result['revision'], READ_RECORDS)
    assert len(result["queries"]["records"]) == 1
    record = result["queries"]["records"][0]
    assert result['revision'] == original_revision + 1
    assert record["id"] == new_id
    assert record["name"] == "andrea"


def test_delete():
    storage = get_storage()
    result = storage.push_actions(0, CREATE_RECORD)
    original_revision = result['revision']
    new_id = result['new_ids']["a"]
    result = storage.push_actions(result['revision'], READ_RECORDS)
    result = storage.push_actions(result['revision'], {
        'delete': [
            {
                "key": new_id,
                "path": "records"
            }
        ]
    })
    result = storage.push_actions(result['revision'], READ_RECORDS)
    assert result['revision'] == original_revision + 1
    assert len(result["queries"]["records"]) == 0


def test_transaction_commit():
    storage = get_storage()
    transaction_id = storage.start_transaction()['transaction_id']
    result = storage.push_actions(0, CREATE_RECORD, transaction_id)
    storage.commit_transaction(transaction_id)
    result = storage.push_actions(result['revision'], READ_RECORDS)
    assert len(result["queries"]["records"]) == 1
    record = result["queries"]["records"][0]
    assert record["name"] == "tim"


def test_transaction_abort():
    storage = get_storage()
    result = storage.start_transaction()
    transaction_id = result['transaction_id']
    original_revision = result['revision']
    result = storage.push_actions(result['revision'], CREATE_RECORD, transaction_id)
    result = storage.push_actions(result['revision'], CREATE_RECORD, transaction_id)
    result = storage.abort_transaction(transaction_id)
    result = storage.push_actions(result['revision'], READ_RECORDS)
    assert len(result["queries"]["records"]) == 0
    assert result['revision'] == original_revision


def test_raises_error_when_transaction_timed_out():
    storage = get_storage()
    result = storage.start_transaction(0)
    original_revision = result['revision']
    transaction_id = result['transaction_id']
    with pytest.raises(ApiError) as err:
        result = storage.push_actions(result['revision'], CREATE_RECORD, transaction_id)
    assert err.value.code == 'transaction_timed_out'
    assert result['revision'] == original_revision


def test_raises_error_when_transaction_in_progress():
    storage = get_storage()
    result = storage.start_transaction()
    original_revision = result['revision']
    with pytest.raises(ApiError) as err:
        result = storage.push_actions(result['revision'], CREATE_RECORD, None)
    assert err.value.code == 'transaction_in_progress'
    assert result['revision'] == original_revision


def test_raises_error_when_no_transaction_in_progress():
    storage = get_storage()
    result = storage.push_actions(0, CREATE_RECORD)
    original_revision = result['revision']
    transaction_id = 12345
    with pytest.raises(ApiError) as err:
        result = storage.push_actions(result['revision'], CREATE_RECORD, transaction_id)
    assert err.value.code == 'no_transaction_in_progress'
    assert result['revision'] == original_revision


def test_raises_error_when_transaction_id_mismatch():
    storage = get_storage()
    result = storage.start_transaction()
    original_revision = result['revision']
    transaction_id = 12345
    with pytest.raises(ApiError) as err:
        result = storage.push_actions(result['revision'], CREATE_RECORD, transaction_id)
    assert err.value.code == 'transaction_id_mismatch'
    assert result['revision'] == original_revision

