from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
from .modelos import db ,User, Document, DocumentFormat
from vistas import VistaSignUp, BistaLogin, VistaTasks


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dbapp.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'MISO-Nube'
app.config['PROPAGATE_EXCEPTIONS'] = True

app_context = app.app_context()
app_context.push()

db.init_app(app)
db.create_all()

cors = CORS(app)

api = Api(app)
api.add_resource(VistaSignUp , '/api/auth/signup')
api.add_resource(BistaLogin  , '/api/auth/login')
api.add_resource(VistaTasks  , '/api/tasks', '/api/tasks/<int:id_task>')

jwt = JWTManager(app)
