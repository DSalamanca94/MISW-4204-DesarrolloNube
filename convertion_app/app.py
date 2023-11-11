from flask import Flask
from flask_restful import Api
from celery_config import celery_init_app

import os
import subprocess
from modelos import db, Document, DocumentStatus
from celery import Celery
from celery.signals import task_postrun
from flask.globals import current_app


_upload_directory = '/app/temp/in'  # Path to the uploaded files
_download_directory = '/app/temp/out'  # Path to the processed files

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

db.init_app(app)

celery = celery_init_app(app)
celery.set_default()

app_context.push()

api = Api(app)

@celery.task(name='convertFiles')
def convertFiles(document_id):
    document = Document.query.get(document_id)
    print('{} - document {} in convertFiles'.format('datetime.datetime.now()', document.id))
    input_filename = document.location_in
    output_filename = f"{document.id}.{document.format_out.value}"
    output_filename = os.path.join(_download_directory, output_filename)

    with open(output_filename, "wb") as out_file:
        out_file.close()

    print(f'{input_filename =}')

    ffmpeg_command = ['ffmpeg', '-i', input_filename, output_filename, '-y']

    return_code = subprocess.call(ffmpeg_command)

    with open(output_filename, "rb") as output_file:
        document.file_out = output_file.read()

    if not return_code:
        document.status = DocumentStatus.Ready
    else:
        document.status = DocumentStatus.Error

    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')