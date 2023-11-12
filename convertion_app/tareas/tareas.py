import datetime
import hashlib
import os
import subprocess
from modelos import db, Document, DocumentStatus
from celery import Celery
from celery.signals import task_postrun
from flask.globals import current_app

_upload_directory = '/app/temp/in'  # Path to the uploaded files
_download_directory = '/app/temp/out'  # Path to the processed files

# celery_ = Celery(__name__)

import json
from os.path import abspath, dirname, join

config_file_path = abspath(join(dirname(__file__), '..', 'config.json'))

with open(config_file_path, 'r') as config_file:
    config_data = json.load(config_file)

celery_ = Celery('tasks', broker= f"redis://{config_data['IpRedis']}:6379/0")


@celery_.task(name = 'convertFiles')
def convertFiles( document_id ):
    document = Document.query.get(document_id)
    print('{} - document {} in convert Files'.format('datetime.datetime.now()', document.id))
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

    # return_code = 0
    
    if not return_code:
        document.status = DocumentStatus.Ready

    else :
        document.status = DocumentStatus.Error

    db.session.commit()
