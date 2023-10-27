from celery import Celery
from modelos import db, Document
import subprocess
import os

_base = os.path.dirname(os.path.abspath(__file__))
_base = os.path.dirname(_base)
_download_directory = os.path.join(_base, 'temp', 'out')

celery_app = Celery(__name__, broker='redis://localhost:6379/0')

@celery_app.task()
def convert_document(document_id):
    document = Document.query.get(document_id)

    if not document:
        return {'error': 'Document not found'}, 404

    # Define the input and output file paths
    input_filename = document.location_in
    output_filename = os.path.join(_download_directory, f"{document.id}.{document.format_out.value}")

    try:
        # Use FFmpeg to convert the document format
        ffmpeg_command = [
            'ffmpeg',
            '-i', input_filename,
            output_filename,
            '-y',  # Overwrite the output file if it exists
        ]

        return_code = subprocess.call(ffmpeg_command)

        if return_code == 0:
            # Conversion successful
            with open(output_filename, "rb") as output_file:
                document.file_out = output_file.read()
            db.session.commit()
            return 'Document conversion completed'
        else:
            # Conversion failed
            return {'error': 'Document conversion failed'}, 500

    except Exception as e:
        return {'error': str(e)}, 500
