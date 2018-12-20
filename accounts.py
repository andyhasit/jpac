from utils import JsonFileWrapper, ApiError

'''
from cryptography.fernet import Fernet
key = Fernet.generate_key() #this is your "password"
cipher_suite = Fernet(key)
encoded_text = cipher_suite.encrypt(b"Hello stackoverflow!")
decoded_text = cipher_suite.decrypt(encoded_text)
'''

class AccountRegister:

    def __init__(self, db_path):
        self._db = JsonFileWrapper(db_path)
        self._data = None

    def _load(self):
        self._data = self._db.load()

    def _save(self):
        self._db.save(self._data) # TODO no arg?

    def _encrypt(self, password):
        return password * 2

    def create_account(self, user, password):
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

    def change_password(self, user, password):
        self._data['accounts'][user]['password'] = self._encrypt(password)
        self._save()
