# try:
import os
from flask import Flask
from flask_restx import Api
from flask_cors import CORS
# import flask.scaffold
# except ImportError as exc:
#     os.system('python -m pip install {}'.format(exc.name))
#     os.system('python ./app.py')

# flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
app = Flask(__name__)
app.config.from_object('config.Default')
apiConfig = {
    'doc': '/' if app.config['SWAGGER_DOC'] else False,
    'validate': app.config['RESTPLUS_VALIDATE']
}
cors = CORS(app, resources={r"/*": {"origins": "*"}})
api = Api(app, **apiConfig)
