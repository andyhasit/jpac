import os
import pytest
import shutil
from datetime import datetime
from ..accounts import AccountRegister
from .utils_for_tests import wipe_json_dbs, tmp_db_file


@pytest.fixture(scope="session", autouse=True)
def my_fixture():
    wipe_json_dbs(tmp_db_file())

def new_account_register():
    return AccountRegister(tmp_db_file('account_register'))

def test_create_user():
    ar = new_account_register()
    ar.create_user('bob', '1234')
    assert ar.user_exists('bob')
    assert not ar.user_exists('not bob')


'''
   def create_user(self, user, password):
        self._load()
        if user in self._data['accounts']:
            raise ApiError(code="account_exists")
        self._data['accounts'][user] = {
            'password': self._encrypt(password),
            'apps': []
        }
        self._save()

    def user_exists(self, user):
        self._load()
        return user in self._data['accounts']

    def has_account_for_app(self, app, user):
        return user in self._data['accounts'] and app in self._data['accounts'][user]['apps']

    def add_user_app(self, app, user):
        apps_list = self._data['accounts'][user]['apps']
        if app not in apps_list:
            apps_list.append(app)
        self._save()

    def remove_user_app(self, app, user):
        apps_list = self._data['accounts'][user]['apps']
        if app in apps_list:
            apps_list.remove(app)
        self._save()

    def password_matches(self, user, password):
        return self._data['accounts'][user]['password'] == self._encrypt(password)

    def change_password
'''