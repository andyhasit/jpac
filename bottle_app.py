from bottle import default_app, route, template, static_file, request, response,\
    HTTPError
from json_storage import ApiError, MyJsonStorageHandler


JSON_BASE = '/home/andyhasit/pointy/json_dbs'

application = default_app()

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


def check(user, pw):
    # Check user/pw here and return True/False
    return user == 'me' and pw =='poo'


@route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root='/static')


@route('/', method = 'OPTIONS')
@route('/<path:path>', method = 'OPTIONS')
def options_handler(path = None):
    return


@route('/')
def index():
    return template('index')


storage_containers = {}

@route('/<app>/actions', method='POST')
def actions(app):
    return wrap_storage_call(request, app, 'do_actions', request.json)


def get_storage(app, user):
    if user != 'tim':
        raise HTTPError(401, 'Invalid login')
    key = (app, user)
    if key in storage_containers:
        storage = storage_containers[key]
    else:
        storage = MyJsonStorageHandler()
        storage.set_paths(JSON_BASE, '{}____{}'.format(*key))
        storage_containers[key] = storage
    return storage


def wrap_storage_call(request, app, method, params):
    """
    Generic wrapper for all storage calls.
    """
    try:
        user, password = request.auth or (None, None)

        '''
        err = HTTPError(401, text)
        err.add_header('WWW-Authenticate','')
        '''
        #TODO: wrap in try execpt which validates user too
        storage = get_storage(app, user)
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
