from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
from flask_apscheduler import APScheduler
from vistas import VistaSignUp, VistaLogin, VistaTasks, VistaStatus, DocumentDownloadIn, DocumentDownloadOut,VistaUsers
from config import config
from celery_config import celery_init_app


app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'MISO-Nube'
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['CELERY_CONFIG'] = {
    "broker_url":'redis://redis:6379/0',
    "result_backend":'redis://redis:6379/0',
}

# Initialize the application context
app_context = app.app_context()
app_context.push()


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
api.add_resource(VistaUsers, '/api/users')


jwt = JWTManager(app)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.run(debug=True, host='0.0.0.0')