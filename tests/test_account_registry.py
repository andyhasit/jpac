from cryptography.fernet import Fernet
from ..accounts import AccountRegister
from .utils_for_tests import wipe_json_dbs, tmp_db_file

'''
@pytest.fixture(scope="session", autouse=True)
def my_fixture():
    wipe_json_dbs()
'''

# Sava as string as that's how it will be stored in file
SECRET_KEY = str(Fernet.generate_key(), 'UTF-8')


def new_account_register():
    return AccountRegister(SECRET_KEY, tmp_db_file('account_register'))


def test_create_user():
    ar = new_account_register()
    ar.create_user('bob', '1234')
    assert ar.user_exists('bob')
    assert not ar.user_exists('not bob')


def test_add_user_app():
    ar = new_account_register()
    ar.create_user('bob', '1234')
    ar.add_user_app('bob', 'app1')
    assert ar.has_account_for_app('bob', 'app1')
    assert not ar.has_account_for_app('bob', 'app2')

    ar.add_user_app('bob', 'app2')
    assert ar.has_account_for_app('bob', 'app1')
    assert ar.has_account_for_app('bob', 'app2')

    ar.remove_user_app('bob', 'app1')
    assert not ar.has_account_for_app('bob', 'app1')
    assert ar.has_account_for_app('bob', 'app2')


def test_password_matching():
    ar = new_account_register()
    ar.create_user('bob', '1234')
    assert ar.password_matches('bob', '1234')
    assert not ar.password_matches('bob', '12344567')

    ar.change_password('bob', 'new_pass')
    assert ar.password_matches('bob', 'new_pass')
    assert not ar.password_matches('bob', '1234')

