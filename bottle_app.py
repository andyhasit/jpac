import os
from bottle import default_app, route, template, static_file, request, response,\
    HTTPError
from json_storage import MyJsonStorageHandler
from accounts import AccountRegister
from utils import ApiError

JSON_BASE = '/home/andyhasit/pointy/json_dbs'
JSON_STORES = {}
PASSWORDS = {
    ('pointy_v2', 'andyhasit') : 'frickingawesome45'
    }

ACCOUNT_REGISTER = AccountRegister('/home/andyhasit/pointy/json_dbs/accounts.json')

VALID_APPS = (
    'pointy_v2',
)

VALID_METHODS = (
    'push_actions',
    'start_transaction',
    'abort_transaction',
    'commit_transaction'
)


def validate_user(app, user, password):
    if not ACCOUNT_REGISTER.has_account_for_app(app, user):
        raise HTTPError(403, 'No account for user {} in app {}'.format(user, app))
    if not ACCOUNT_REGISTER.password_matches(user, password):
        err = HTTPError(401, 'Invalid login')
        err.add_header('WWW-Authenticate','')
        raise err


def get_storage(app, user):
    key = (app, user)
    if key in JSON_STORES:
        storage = JSON_STORES[key]
    else:
        data_db_path = os.path.join(JSON_BASE, app, user, 'data.json')
        meta_data_db_path = os.path.join(JSON_BASE, app, user, 'meta_data.json')
        storage = MyJsonStorageHandler(data_db_path, meta_data_db_path)
        JSON_STORES[key] = storage
    return storage


def validate_app_method(app, method):
    if app not in VALID_APPS:
        raise HTTPError(404, 'App {} does not exist'.format(app))
    if method not in VALID_METHODS:
        raise HTTPError(404, 'App {} does not exist'.format(app))


def wrap_storage_call(request, app, method, params):
    """
    Generic wrapper for all storage calls.
    """
    try:
        user, password = request.auth or (None, None)
        validate_app_method(app, method)
        validate_user(app, user, password)
        storage = get_storage(app, user, password)
        result = getattr(storage, method)(**params)
        return {
            "status" : "success",
            "data" : result
        }
    except ApiError as e:
        return {
            "status" : "fail",
            "data" : {
                "code": e.code,
                "message": str(e),
                "data": e.data
            }
        }
    except HTTPError as e:
        return e
    except BaseException as e:
        return {
            "status" : "error",
            "data" : {
                "type": str(type(e)),
                "message": str(e)
            }
        }

application = default_app()


# Enables CORS
@application.hook('after_request')
def enable_cors():
    """
    You need to add some headers to each request.
    Don't use the wildcard '*' for Access-Control-Allow-Origin in production.
    """
    response.headers['Access-Control-Allow-Origin'] = '*' # 'http://localhost:100'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Origin, Accept, Content-Type, X-Requested-With'
    #'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'


# For pre-flight options
@route('/', method = 'OPTIONS')
@route('/<path:path>', method = 'OPTIONS')
def options_handler(path = None):
    return


# For static files
@route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root='/static')


# For the home page
@route('/')
def index():
    return template('index')


# The app's API actions
@route('/<app>/<method>', method='POST')
def app_method(app, method):
    return wrap_storage_call(request, app, method, request.json)

