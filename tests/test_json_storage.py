import os
from ..json_storage import *

JSON_BASE = os.path.join(os.path.dirname(__file__), 'json_dbs')

def test_tests_run():
    storage = MyJsonStorageHandler()
    storage.set_paths(JSON_BASE, 'test')
    storage.load()

