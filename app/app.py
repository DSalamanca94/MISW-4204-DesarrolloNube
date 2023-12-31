from flask import Flask, send_file
from os import environ
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_restful import Api
from modelos import db
from celery_config import celery_init_app
from vistas import VistaSignUp, VistaLogin, VistaTasks, VistaStatus, DocumentDownloadIn, DocumentDownloadOut

import json
from os.path import abspath, dirname, join

config_file_path = abspath(join(dirname(__file__), '..', 'config.json'))

with open(config_file_path, 'r') as config_file:
    config_data = json.load(config_file)



app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://postgres:postgres@{config_data['IpPostgres']}:5432/postgres"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'MISO-Nube'
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['CELERY_CONFIG'] = {
    "broker_url": f"redis://{config_data['IpRedis']}:6379/0",
    "result_backend": f"redis://{config_data['IpRedis']}:6379/0",
}

# Initialize the application context
app_context = app.app_context()
app_context.push()

db.init_app(app)

celery = celery_init_app(app)
celery.set_default()

app_context.push()

cors = CORS(app)

api = Api(app)
api.add_resource(VistaSignUp, '/api/auth/signup')
api.add_resource(VistaLogin, '/api/auth/login')
api.add_resource(VistaTasks, '/api/tasks', '/api/tasks/<int:id_task>')
api.add_resource(VistaStatus, '/status')
api.add_resource(DocumentDownloadIn, '/api/tasks/<int:id_task>/downloadin')
api.add_resource(DocumentDownloadOut, '/api/tasks/<int:id_task>/downloadout')

jwt = JWTManager(app)

migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')