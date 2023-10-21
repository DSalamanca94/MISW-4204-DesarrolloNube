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
# from ffmpeg import 
import ffmpeg  
from io import BytesIO

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
                return {'filename': filename, 
                    'error': f'same fiel format {format_in}, {format_out}'}, 300
             
            document = Document(
                user_id = user_id,
                filename = filename,
                timestamp = datetime.datetime.now() ,
                status = DocumentStatus.InQueue ,
                format_in =  format_in,
                format_out =  format_out,
                file_in = file.read() ,
                file_out = None
            )

            db.session.add(document)
            db.session.commit()

            return {'filename': filename, 
                    'id': document.id,
                    'timestamp': document.timestamp, 
                    'status': DocumentStatus.InQueue.value}
        
        except Exception as e:
            print(e)
            return {'error': str(e)}, 400



class ConvertDocument_(Resource):
    @jwt_required()
    def get(self, document_id):
        try:
            user_id = get_jwt_identity()
            document = Document.query.get(document_id)

            if not document:
                return {'error': 'Document not found'}, 404

            if document.user_id != user_id:
                return {'error': 'Unauthorized access to this document'}, 403

            if document.status != DocumentStatus.InQueue:
                return {'error': 'Document is not in the queue for conversion'}, 400

            if document.format_in != document.format_out:

                input_filename = f"input_{document.id}.{document.format_in}"
                output_filename = f"output_{document.id}.{document.format_out}"

                with open(input_filename, "wb") as input_file:
                    input_file.write(document.file_in)

                ff = ffmpeg.input(input_filename).output(output_filename)
                
                ff.run()

                with open(output_filename, "rb") as output_file:
                    document.file_out = output_file.read()

                document.status = DocumentStatus.Completed

                os.remove(input_filename)
                os.remove(output_filename)

                db.session.commit()

            return send_file(BytesIO(document.file_out), as_attachment=True, download_name=f"converted_{document.filename}")

        except Exception as e:
            print('error', e)
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

            if document.status == DocumentStatus.InProgress:
                return {'error': 'Document is  in the queue for conversion'}, 201

            if document.format_in != document.format_out:

                print(type(document.file_in))

                file_in = BytesIO(document.file_in)

                print(file_in)

                # input_stream = ffmpeg.input('pipe:', format=str(document.format_in))

                # output_format = document.format_out.value

                # print(f'{ output_format = }')
                
                # output_stream = ffmpeg.output(input_stream, 'pipe:', format=output_format)

                # print(f'{ output_stream = }')

                output_data = BytesIO()

                # stream  = ffmpeg.input('pipe:0',file_in ,format=document.format_in.value)

                # stream  =  ffmpeg.output(stream, output_data ,format=document.format_out.value)

                ffmpeg.input('pipe:0', format='mp4', vcodec='copy').output('pipe:1', format='m2v').run(input=file_in, stdout=output_data)

                output_bytes = output_data.getvalue()

                print(output_data)

                document.file_out = output_data
                
                document.status = DocumentStatus.Completed

                db.session.commit()

            # Return the converted file as a response
            return send_file(BytesIO(document.file_out), as_attachment=True, download_name=f"converted_{document.filename}")

        except Exception as e:
            print('error', e)
            return {'error': str(e)}, 400
