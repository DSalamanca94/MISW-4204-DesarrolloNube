from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
from flask_apscheduler import APScheduler
from modelos import db, User, Document, DocumentFormat
from vistas import VistaSignUp, VistaLogin, VistaTasks, VistaStatus, ConvertDocument, ConvertDocument_function

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dbapp.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'MISO-Nube'
app.config['PROPAGATE_EXCEPTIONS'] = True

# Initialize the application context
app_context = app.app_context()
app_context.push()

db.init_app(app)
db.create_all()

cors = CORS(app)

api = Api(app)
api.add_resource(VistaSignUp, '/api/auth/signup')
api.add_resource(VistaLogin, '/api/auth/login')
api.add_resource(VistaTasks, '/api/tasks', '/api/tasks/<int:id_task>')
api.add_resource(VistaStatus, '/status')
api.add_resource(ConvertDocument, '/api/documents/<int:document_id>')

jwt = JWTManager(app)

app.config.from_object(Config())

# Initialize and start the APScheduler within the application context
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Add your job to the scheduler
scheduler.add_job(id='job1', func=ConvertDocument_function, trigger='interval', minutes=1)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')