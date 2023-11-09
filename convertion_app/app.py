from flask import Flask
from flask_restful import Api
from celery_config import celery_init_app

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@pgsql:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

api = Api(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')