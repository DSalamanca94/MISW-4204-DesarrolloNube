import datetime
import hashlib
import os
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from modelos import db, Document, DocumentStatus, User
from flask import jsonify, request, make_response, send_file, send_from_directory
from flask_restful import Resource
import subprocess
from celery import Celery

_base = os.path.dirname(os.path.abspath(__file__))
_base = os.path.dirname(_base)
_upload_directory = os.path.join(_base, 'temp', 'in')
_download_directory = os.path.join(_base, 'temp', 'out')


celery_app = Celery(__name__, broker='redis://localhost:6379/0')

if not os.path.exists(_upload_directory):
    os.makedirs(_upload_directory)

if not os.path.exists(_download_directory):
    os.makedirs(_download_directory)

@celery_app.task()
def convertFiles(document_id):
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
    
    if not return_code:
        document.status = DocumentStatus.Ready

    else :
        document.status = DocumentStatus.Error

    db.session.commit()

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

            print(user_id)

            if format_in == format_out:
                return {'filename': filename, 'error': f'same file format {format_in}, {format_out}'}, 300

            document = Document(
                user_id = user_id,
                filename = file.filename,
                timestamp = datetime.datetime.now() ,
                status = DocumentStatus.InQueue ,
                format_in =  format_in,
                format_out =  format_out,
                location_in =  ''
            )

            db.session.add(document)
            db.session.commit()

            save_path = os.path.join(_upload_directory, '{}.{}'.format(document.id,format_in ))

            document.location_in = save_path
            file.save(save_path)
            db.session.commit()
            return {'filename': document.filename, 
                    'id': document.id,
                    'timestamp': document.timestamp, 
                    'status': document.status.value}
        
        except Exception as e:
            print(e)
            return {'error': str(e)}, 400


    @jwt_required()
    def get(self, id_task = None):
        if id_task:
            document = Document.query.get(id_task)

            if document is None:
                return {"error": "Documento no encontrado"}, 404

            document_data = {
                "id": document.id,
                "filename": document.filename,
                "timestamp": document.timestamp,
                "status": document.status.value,
                "inputFormat": document.format_in.value,
                "outputFormat": document.format_out.value,
                "loadedFile": f"/api/tasks/{id_task}/downloadin",
                "transformedFile": f"/api/tasks/{id_task}/downloadout"
            }
            return document_data, 200
        
        else:
            # Obtiene el ID del usuario desde el token
            usuario_id = get_jwt_identity()
            # Consulta las tareas del usuario actual
            tareas_usuario = Document.query.filter_by(user_id=usuario_id).all()
            # Formatea las tareas y envíalas como respuesta
            tareas_formateadas = [{
                "id": tarea[0],
                "nombre": tarea[1],
                "extension_original": tarea[2],
                "extension_destino": tarea[3],
                "disponible": tarea[4]
            } for tarea in tareas_usuario]

            return jsonify(tareas_formateadas), 200
    
    def delete(self, id_task):
        document = Document.query.get(id_task)
        if document is None:
            return {"error": "Documento no encontrado"}, 404
        db.session.delete(document)
        db.session.commit()
        return {"mensaje": "Documento eliminado"}, 204

# Estas vistas fueron creadas para descargar el archivo de entrada y el archivo de salida
class DocumentDownloadOut(Resource):
    # def get(self, id_task):
    #     document = Document.query.get(id_task)
    #     if document is None:
    #         return {"error": "Documento no encontrado"}, 404

    #     file_name = f"{document.id}.{document.format_out.value}"
    #     file_path = os.path.join('temp', 'out', file_name)        

    #     if not os.path.exists(file_path):
    #         return {"error": "El archivo no está disponible para descargar"}, 404

    #     return send_from_directory("temp/out", file_name, as_attachment=True)

    @jwt_required()
    def get(self, id_task):
        try:
            user_id = get_jwt_identity()
            document = Document.query.get(id_task)

            if not document:
                return {'error': 'Document not found'}, 404

            if document.user_id != user_id:
                return {'error': 'Unauthorized access to this document'}, 403
            
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

            print('this sheet has run')
            print(return_code)

            print('out',output_filename)

            db.session.commit()
            return send_file(output_filename, as_attachment=True)

        except Exception as e:
            print('error', e)
            return {'error': str(e)}, 400


class DocumentDownloadIn(Resource):
    def get(self, id_task):
        document = Document.query.get(id_task)
        if document is None:
            return {"error": "Documento no encontrado"}, 404

        file_name = f"{document.id}.{document.format_in.value}"
        file_path = os.path.join('temp', 'in', file_name)        

        if not os.path.exists(file_path):
            return {"error": "El archivo no está disponible para descargar"}, 404

        return send_from_directory("temp/in", file_name, as_attachment=True)


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
            output_filename = f"{document.id}.{document.format_out.value}"
            output_filename = os.path.join(_download_directory, output_filename)

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
            return send_file(output_filename, as_attachment=True)

        except Exception as e:
            print('error', e)
            return {'error': str(e)}, 400
    

def ConvertDocument_function():
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
            