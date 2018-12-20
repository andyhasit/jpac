import os
import pytest
import shutil
from datetime import datetime


JSON_TEST_DIR = os.path.join(os.path.dirname(__file__), 'json_dbs')


def wipe_json_dbs():
    shutil.rmtree(JSON_TEST_DIR)
    os.makedirs(JSON_TEST_DIR)

def tmp_db_file(name):
    return os.path.join(JSON_TEST_DIR, '{}_{}.json'.format(datetime.now().utcnow()), name)