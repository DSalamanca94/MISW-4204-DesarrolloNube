from flask import request, make_response, request
from sqlalchemy.orm import joinedload
from flask.json import jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import datetime
import hashlib
from modelos import db, Document, DocumentStatus, User

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


    @jwt_required()
    def get(self, document_id, file_type):
        current_user_id = get_jwt_identity()
        document = Document.query.filter_by(id=document_id, user_id=current_user_id).first()

        if document is None:
            return {'error': 'Document not found'}, 404
        else:
            file_data = document.file_in
            file_format = document.format_in.value
          

        response = make_response(send_file(file_data, mimetype=f'application/{file_format}', as_attachment=True))
        response.headers["Content-Disposition"] = f"attachment; filename={document.filename}.{file_format}"
        return {'status': document.status.value,
                'format_in': document.format_in.value,
                'format_out': document.format_out.value,
                'File': response}, 200

class VistaProcess(Resource):
    def get(self):
        pass