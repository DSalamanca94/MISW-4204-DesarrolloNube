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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@34.67.210.99:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'MISO-Nube'
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['CELERY_CONFIG'] = {
    "broker_url":'redis://34.145.101.102:6379/0',
    "result_backend":'redis://34.145.101.102:6379/0',
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
    download_from_gcs(document.location_in, input_filename)

    with open(output_filename, "wb") as out_file:
        out_file.close()

    print(f'{input_filename =}')

    ffmpeg_command = ['ffmpeg', '-i', input_filename, output_filename, '-y']

    return_code = subprocess.call(ffmpeg_command)

    with open(output_filename, "rb") as output_file:
        document.file_out = output_file.read()

    # Upload output file to GCS
    upload_to_gcs(output_filename, f'Output/{document.id}.{document.format_out.value}')
    
    document.location_out = output_filename

    if not return_code:
        document.status = DocumentStatus.Ready
    else:
        document.status = DocumentStatus.Error

    db.session.commit()

def download_from_gcs(source_blob_name, destination_file_name):
    """Download a file from Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket('app-storage-folder')
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

def upload_to_gcs(source_file_name, destination_blob_name):
    """Upload a file to Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket('app-storage-folder')
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')