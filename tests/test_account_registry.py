import os
import pytest
import shutil
from datetime import datetime
from ..utils import JsonFileWrapper
from .utils_for_tests import wipe_json_dbs


@pytest.fixture(scope="session", autouse=True)
def my_fixture():
    wipe_json_dbs()

def test_nothing():
    pass
