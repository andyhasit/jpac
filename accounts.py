from cryptography.fernet import Fernet
from pointy.utils import JsonFileWrapper, ApiError


def to_bytes(s):
    """Fernet expects strings as bytearrays"""
    return bytes(s, 'utf-8')


class AccountRegister:

    def __init__(self, secret_key, db_path):
        self._db = JsonFileWrapper(db_path, {'accounts': {}})
        self._data = None
        self._cipher_suite = Fernet(to_bytes(secret_key))

    def create_user(self, username, password):
        self._load()
        if username in self._data['accounts']:
            raise ApiError(code="account_exists")
        self._data['accounts'][username] = {
            'password': self._encrypt(password),
            'apps': []
        }
        self._save()

    def user_exists(self, username):
        try:
            self._assert_user_exists(username)
            return True
        except ApiError:
            return False

    def has_account_for_app(self, username, app):
        self._assert_user_exists(username)
        return username in self._data['accounts'] and app in self._data['accounts'][username]['apps']

    def add_user_app(self, username, app):
        self._assert_user_exists(username)
        apps_list = self._data['accounts'][username]['apps']
        if app not in apps_list:
            apps_list.append(app)
        self._save()

    def remove_user_app(self, username, app):
        self._assert_user_exists(username)
        apps_list = self._data['accounts'][username]['apps']
        if app in apps_list:
            apps_list.remove(app)
        self._save()

    def change_password(self, username, password):
        self._assert_user_exists(username)
        self._data['accounts'][username]['password'] = self._encrypt(password)
        self._save()

    def password_matches(self, username, password):
        self._assert_user_exists(username)
        saved = self._decrypt(self._data['accounts'][username]['password'])
        return saved == to_bytes(password)

    def _assert_user_exists(self, username):
        self._load()
        if username not in self._data['accounts']:
            raise ApiError(code="account_not_found")

    def _encrypt(self, password):
        return self._cipher_suite.encrypt(to_bytes(password))

    def _decrypt(self, password):
        return self._cipher_suite.decrypt(password)

    def _load(self):
        self._data = self._db.load()

    def _save(self):
        self._db.save()