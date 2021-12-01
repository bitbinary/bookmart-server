try:
    import firebase_admin
    import pyrebase
    from firebase_admin import credentials, auth
    import json
    from flask import Flask, request
    from functools import wraps
except:
    import os
    os.system('python -m pip install firebase_admin')
    os.system('python -m pip install pyrebase4')
    import firebase_admin
    import pyrebase
    from firebase_admin import credentials, auth
    import json
    from flask import Flask, request
    from functools import wraps



cred = credentials.Certificate('firebase_admin.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('firebase_config.json')))

def check_token(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided.'},400
        try:
            user = auth.verify_id_token(request.headers['Authorization'])
            request.user = user
            print(user)
        except:
            return {'message':'Invalid token.'},400
        return f(*args, **kwargs)
    return wrap

@check_token
def userinfo():
    print(request.user)
    data={'user_id':request.user['uid']}
    return {data}, 200