from flask import Flask
from flask_restful import Api
from celery_config import celery_init_app

import os
import subprocess
from modelos import db, Document, DocumentStatus
from celery import Celery
from celery.signals import task_postrun
from flask.globals import current_app

from google.cloud import storage
from google.cloud.exceptions import NotFound

_upload_directory = 'gs://app-storage-folder/Input'  # Path to the uploaded files
_download_directory = 'gs://app-storage-folder/Output'


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

api = Api(app)

@celery.task(name='convertFiles')
def convertFiles(document_id):
    document = Document.query.get(document_id)
    print('{} - document {} in convertFiles'.format('datetime.datetime.now()', document.id))
    input_filename = document.location_in
    output_filename = f"{document.id}.{document.format_out.value}"
    output_filename = os.path.join(_download_directory, output_filename)

    # Download input file from GCS
    # download_from_gcs(document.location_in, input_filename)

    # with open(output_filename, "wb") as out_file:
    #     out_file.close()

    local_input_filename = download_from_gcs(document.location_in, document.id)
    local_output_filename = f'{document.id}.{document.format_out.value}'

    ffmpeg_command = ['ffmpeg', '-i', local_input_filename, local_output_filename, '-y']

    return_code = subprocess.call(ffmpeg_command)

    # Upload output file to GCS
    upload_to_gcs(local_output_filename, f'Output/{document.id}.{document.format_out.value}')
    
    document.location_out = output_filename

    if not return_code:
        document.status = DocumentStatus.Ready
    else:
        document.status = DocumentStatus.Error

    db.session.commit()

def download_from_gcs(source_blob_name, document_id):
    """Descargar un archivo desde Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket('app-storage-folder')
    blob = bucket.blob(source_blob_name)
    # Crear un directorio local para cada documento
    local_directory = f'/path/to/local_directory/{document_id}/'
    os.makedirs(local_directory, exist_ok=True)
    # Construir la ruta local del archivo
    local_filename = os.path.join(local_directory, source_blob_name.split('/')[-1])
    # Descargar el archivo al directorio local
    blob.download_to_filename(local_filename)
    return local_filename

def upload_to_gcs(source_file_name, destination_blob_name):
    """Upload a file to Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket('app-storage-folder')
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')