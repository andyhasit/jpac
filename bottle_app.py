import json
import os
from bottle import default_app, route, template, static_file, request, response, auth_basic
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


@route('/')
def index():
    return template('index')

@route('/', method = 'OPTIONS')
@route('/<path:path>', method = 'OPTIONS')
def options_handler(path = None):
    return


@route('/actions', method='POST')
@auth_basic(check)
def actions():
    data = request.json
    storage = MyJsonStorageHandler()
    storage.set_paths(JSON_BASE, 'andyhasit_pointy_v2')
    try:
        result = storage.do_actions(**data)
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
    except BaseException as e:
        return {
            "status" : "error",
            "data" : {
                "type": str(type(e)),
                "message": str(e)
            }
        }
