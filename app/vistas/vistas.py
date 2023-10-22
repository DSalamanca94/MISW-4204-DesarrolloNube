import datetime
import hashlib
import os
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from modelos import db, Document, DocumentStatus, User
from flask import request, make_response, send_file
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from flask_restful import Resource
from flask.json import jsonify
from flask import current_app
# from ffmpeg import 
import ffmpeg  
from io import BytesIO
import atexit
import subprocess

from flask_apscheduler import APScheduler

_upload_directory = os.path.dirname(os.path.abspath(__file__))
_upload_directory = os.path.dirname(_upload_directory)
_upload_directory = os.path.join(_upload_directory, 'temp')

scheduler = APScheduler()

if not os.path.exists(_upload_directory):
    os.makedirs(_upload_directory)

# def start_scheduler(app):
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(ConvertDocument_function, 'interval', minutes=0.5)  # Run the function every 5 minutes
#     scheduler.start()
#     atexit.register(lambda: scheduler.shutdown())

class VistaStatus(Resource):
    def get(self):
        return {'status' : 'Connected'}

class VistaLogin(Resource):
     def post(self):
        password_encriptada = hashlib.md5(request.json["password"].encode('utf-8')).hexdigest()
        user = User.query.filter(User.email == request.json["email"],
                                       User.password == password_encriptada).first()        
        db.session.commit()

        if user is None:
            return "El usuario no existe", 404
        else:
            token_de_acceso = create_access_token(identity=user.id)
            return {"mensaje": "Inicio de sesión exitoso",
                "token": token_de_acceso  
            }


class VistaSignUp(Resource):
    def post(self):        
        user = User.query.filter(User.email == request.json["email"]).first()      
        if user is None:
            pass_or = request.json["password"]
            pass_cn = request.json["password_conf"]
            if pass_or != pass_cn:
                return "La confirmacación de contraseaña no es correcta.", 404
            password_encriptada = hashlib.md5(request.json["password"].encode('utf-8')).hexdigest()            
            nuevo_user = User(user=request.json["user"], email=request.json["email"], password=password_encriptada) 
            db.session.add(nuevo_user)
            db.session.commit()
            token_de_acceso = create_access_token(identity=nuevo_user.id)
            return {"mensaje": "usuario creado exitosamente", "id": nuevo_user.id}
        else:
            return "El usuario ya existe", 404


class VistaTasks(Resource):
    @jwt_required()
    def post(self):
        try:
            user_id = get_jwt_identity()
            file = request.files['file']
            format_out = request.form.get('format')
            filename, format_in = file.filename.split('.')

            if format_in == format_out:
                return {'filename': filename, 'error': f'same file format {format_in}, {format_out}'}, 300
            
            timestamp = datetime.datetime.today()
            print(str(timestamp).replace(" ", ""))
            print("{}.{}".format( str(timestamp).replace(" ", ""),  format_in) )
            # save_path = os.path.join(_upload_directory, "{}.{}".format( str(timestamp).replace(" ", ""),  format_in, format_in) )
            save_path = os.path.join(_upload_directory, file.filename)
            
            file.save(save_path)

            document = Document(
                user_id = user_id,
                filename = file.filename,
                timestamp = datetime.datetime.now() ,
                status = DocumentStatus.InQueue ,
                format_in =  format_in,
                format_out =  format_out,
                location_in =  save_path,
                file_in = None ,
                file_out = None
            )

            db.session.add(document)
            db.session.commit()

            return {'filename': document.filename, 
                    'id': document.id,
                    'timestamp': document.timestamp, 
                    'status': document.status.value}
        
        except Exception as e:
            print(e)
            return {'error': str(e)}, 400

class ConvertDocument(Resource):
    @jwt_required()
    def get(self, document_id):
        try:
            user_id = get_jwt_identity()
            document = Document.query.get(document_id)

            if not document:
                return {'error': 'Document not found'}, 404

            if document.user_id != user_id:
                return {'error': 'Unauthorized access to this document'}, 403
            
            input_filename = document.location_in
            output_filename = f"output_{document.id}.{document.format_out.value}"

            with open(output_filename, "wb") as out_file:
                out_file.close()

            print(f'{input_filename =}')

            ffmpeg_command = ['ffmpeg', '-i', input_filename, output_filename, '-y']

            return_code = subprocess.call(ffmpeg_command)

            with open(output_filename, "rb") as output_file:
                document.file_out = output_file.read()

            print('this sheet has run')
            print(return_code)

            print('out',output_filename)

            db.session.commit()
            # os.remove(output_filename)

            return send_file(output_filename, as_attachment=True)
        
        except Exception as e:
            print('error', e)
            return {'error': str(e)}, 400
        
# @scheduler.task('interval', id='job1', minutes=1)
def ConvertDocument_function():
    with scheduler.app.app_context():
        print('Execution')
        document = Document.query.filter_by(status = DocumentStatus.InQueue).first

    def get(self, document_id):
        try:
            user_id = get_jwt_identity()
            document = Document.query.get(document_id)

            if not document:
                return {'error': 'Document not found'}, 404

            if document.user_id != user_id:
                return {'error': 'Unauthorized access to this document'}, 403
            
            input_filename = document.location_in
            output_filename = f"output_{document.id}.{document.format_out.value}"

            with open(output_filename, "wb") as out_file:
                out_file.close()

            print(f'{input_filename =}')

            ffmpeg_command = ['ffmpeg', '-i', input_filename, output_filename, '-y']

            return_code = subprocess.call(ffmpeg_command)

            with open(output_filename, "rb") as output_file:
                document.file_out = output_file.read()

            print('this sheet has run')
            print(return_code)

            print('out',output_filename)

            db.session.commit()
            # os.remove(output_filename)

            return send_file(output_filename, as_attachment=True)
        
        except Exception as e:
            print('error', e)
            return {'error': str(e)}, 400
            