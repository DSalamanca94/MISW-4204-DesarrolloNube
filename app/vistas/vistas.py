from flask import request, make_response, request
from sqlalchemy.orm import joinedload
from flask.json import jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import datetime
from modelos import db, Document, DocumentStatus

class VistaStatus(Resource):
    def get(self):
        return {'status' : 'Connected'}

class VistaLogin(Resource):
    pass


class VistaSignUp(Resource):
    pass


class VistaTasks(Resource):
    # @jwt_required
    def post(self):
        try:
            # TODO
            # ADD the user who owns the file
            # TODO
            file = request.files['file']
            format_out = request.form.get('format')
            filename, format_in = file.filename.split('.')

            if format_in == format_out:
                return {'filename': filename, 
                    'error': f'same fiel format {format_in}, {format_out}'}, 300
             
            document = Document(
                user_id = None, #TODO
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
        
    def get(self):
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



class VistaProcess(Resource):
    def get(self):
        pass