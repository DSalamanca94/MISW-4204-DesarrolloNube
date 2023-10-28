import datetime
import hashlib
import os
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask import jsonify, request, make_response, send_from_directory
from flask_restful import Resource
import subprocess
from celery import shared_task
from celery.contrib.abortable import AbortableTask


# -----
from database.db import get_connection
from entities import Usuario, Documento ,DocumentStatus


_upload_directory = '/app/temp/in'  # Path to the uploaded files
_download_directory = '/app/temp/out'  # Path to the processed files


if not os.path.exists(_upload_directory):
    os.makedirs(_upload_directory)

if not os.path.exists(_download_directory):
    os.makedirs(_download_directory)

@shared_task(bind = True, base = AbortableTask)

def convertFiles(self, document_id):
    try:
        conn=get_connection()
        with conn.cursor() as cursor:
            cursor.execute("select * from document where id=%s",(document_id,))
            resultset = cursor.fetchall()
            if len(resultset) == 0:
                return make_response(jsonify({'mensaje': 'El documento no existe'}), 401)
            else:
                document=Documento(resultset[0][0],resultset[0][1],resultset[0][2],resultset[0][3],resultset[0][4],resultset[0][5],resultset[0][6])
                input_filename = document.location_in
                output_filename = f"{document.id}.{document.format_out}"
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
                
                cursor.execute("update document set status=%s where id=%s",(document.status,document.id))
                conn.commit()
                conn.close()
    except Exception as ex:
        raise Exception(ex)

class VistaUsers(Resource):
    def get(self):
        try:
            conn = get_connection()
            usuarios = []

            with conn.cursor() as cursor:
                cursor.execute("select * from userlogin")
                resultset = cursor.fetchall()

                for row in resultset:
                    usuario=Usuario(row[0],row[1],row[2],row[3])
                    usuarios.append(usuario.to_JSON())
                conn.close()
            return jsonify(usuarios)
        except Exception as ex:
            raise Exception(ex)

class VistaStatus(Resource):
    def get(self):
        return {'status' : 'Connected'}

class VistaLogin(Resource):
      def post(self):
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("select * from userlogin where useremail=%s and userpassword=%s",(request.json["email"],hashlib.md5(request.json["password"].encode('utf-8')).hexdigest()))
                resultset = cursor.fetchall()
                if len(resultset) == 0:
                    return make_response(jsonify({'mensaje': 'el usuario no existe'}), 401)
                else:
                    user_id = resultset[0][0]
                    token_de_acceso = create_access_token(identity=user_id)
                    conn.close()
                    return make_response(jsonify({'mensaje': 'Inicio de sesión exitoso',
                                                  "token": token_de_acceso              
                                                  }), 200)
                
        except Exception as ex:
            raise Exception(ex)

class VistaSignUp(Resource):
    def post(self):
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("select * from userlogin where useremail=%s",(request.json["email"],))
                resultset = cursor.fetchall()
                if len(resultset) == 0:
                    pass_or = request.json["password"]
                    pass_cn = request.json["password_conf"]
                    if pass_or != pass_cn:
                        return make_response(jsonify({'mensaje': 'La confirmacación de contraseaña no es correcta.'}), 401)
                    password_encriptada = hashlib.md5(request.json["password"].encode('utf-8')).hexdigest()
                    cursor.execute("insert into userlogin(username,useremail,userpassword) values(%s,%s,%s)",(request.json["user"],request.json["email"],password_encriptada))
                    conn.commit()
                    conn.close()
                    return make_response(jsonify({'mensaje': 'usuario creado exitosamente'}), 200)
                else:
                    conn.close()
                    return make_response(jsonify({'mensaje': 'El usuario ya existe'}), 401)
        except Exception as ex:
            raise Exception(ex)

class VistaTasks(Resource):

    @jwt_required()
    def post(self):
        try:
            user_id=get_jwt_identity()
            file=request.files['file']
            format_out=request.form['format']
            filename=file.filename
            format_in=file.filename.split(".")[1]
            timestamp=datetime.datetime.now()
            status = DocumentStatus.InQueue.value
            location_in = ""
            
            conn=get_connection()
            with conn.cursor() as cursor:
                cursor.execute("insert into document(user_id,filename,timestamp,status,format_in,format_out,location_in) values(%s,%s,%s,%s,%s,%s,%s)",(user_id,filename,timestamp,status,format_in,format_out,location_in))
                conn.commit()
                cursor.execute("select * from document where timestamp=%s and user_id=%s",(str(timestamp),user_id))
                resultset = cursor.fetchall()
                task_id = resultset[0][0]
               
                save_path = os.path.join(_upload_directory, f'{task_id}.{format_in}')
                cursor.execute("update document set location_in=%s where id=%s",(save_path,task_id))
                conn.commit()
                conn.close()
              
            #file.save(save_path)

            return make_response(jsonify({'filename':filename,'id': task_id,'timestamp':timestamp,"status":status ,'mensaje': 'Tarea creada exitosamente'}), 200)

        except Exception as ex:
            raise Exception(ex)

    
    @jwt_required()
    def get(self, id_task = None):
        try:
            user_id = get_jwt_identity()
            conn = get_connection()
            with conn.cursor() as cursor:
                if id_task is None:
                    cursor.execute("select * from document where user_id=%s",(user_id,))
                    resultset = cursor.fetchall()
                    documentos = []
                    for row in resultset:
                        documento=Documento(row[0],row[1],row[2],row[3],row[4],row[5],row[6])
                        documentos.append(documento.to_JSON())
                    return jsonify(documentos)
                else:
                    cursor.execute("select * from document where id=%s",(id_task,))
                    resultset = cursor.fetchall()
                    if len(resultset) == 0:
                        return make_response(jsonify({'mensaje': 'El documento no existe'}), 401)
                    else:
                        documento=Documento(resultset[0][0],resultset[0][1],resultset[0][2],resultset[0][3],resultset[0][4],resultset[0][5],resultset[0][6])
                        return jsonify(documento.to_JSON())
        except Exception as ex:
            raise Exception(ex)

    
    def delete(self, id_task):
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("select * from document where id=%s",(id_task,))
                resultset = cursor.fetchall()
                if len(resultset) == 0:
                    return make_response(jsonify({'mensaje': 'El documento no existe'}), 401)
                else:
                    cursor.execute("delete from document where id=%s",(id_task,))
                    conn.commit()
                    return make_response(jsonify({'mensaje': 'El documento fue eliminado'}), 200)
        except Exception as ex:
            raise Exception(ex)

# Estas vistas fueron creadas para descargar el archivo de entrada y el archivo de salida
class DocumentDownloadOut(Resource):
    def get(self, id_task):
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("select * from document where id=%s",(id_task,))
                resultset = cursor.fetchall()
                if len(resultset) == 0:
                    return make_response(jsonify({'mensaje': 'El documento no existe'}), 401)
                
                file_name = f"{resultset[0][0]}.{resultset[0][5]}"
                file_path = os.path.join('temp', 'out', file_name)

                if not os.path.exists(file_path):
                    return {"error": "El archivo no está disponible para descargar"}, 404
                return send_from_directory("temp/out", file_name, as_attachment=True)
        except Exception as ex:
            raise Exception(ex)

class DocumentDownloadIn(Resource):
    def get(self, id_task):
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("select * from document where id=%s",(id_task,))
                resultset = cursor.fetchall()
                if len(resultset) == 0:
                    return make_response(jsonify({'mensaje': 'El documento no existe'}), 401)
                
                file_name = f"{resultset[0][0]}.{resultset[0][4]}"
                file_path = os.path.join('temp', 'in', file_name)

                if not os.path.exists(file_path):
                    return {"error": "El archivo no está disponible para descargar"}, 404
                return send_from_directory("temp/in", file_name, as_attachment=True)
        except Exception as ex:
            raise Exception(ex)
