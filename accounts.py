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

    def _load(self):
        self._data = self._db.load()

    def _save(self):
        self._db.save()

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

    def has_account_for_app(self, user, app):
        return user in self._data['accounts'] and app in self._data['accounts'][user]['apps']

    def add_user_app(self, user, app):
        apps_list = self._data['accounts'][user]['apps']
        if app not in apps_list:
            apps_list.append(app)
        self._save()

    def remove_user_app(self, user, app):
        apps_list = self._data['accounts'][user]['apps']
        if app in apps_list:
            apps_list.remove(app)
        self._save()

    def change_password(self, user, password):
        self._data['accounts'][user]['password'] = self._encrypt(password)
        self._save()

    def password_matches(self, user, password):
        saved = self._decrypt(self._data['accounts'][user]['password'])
        return saved == to_bytes(password)

    def _encrypt(self, password):
        return self._cipher_suite.encrypt(to_bytes(password))

    def _decrypt(self, password):
        return self._cipher_suite.decrypt(password)

