from flask import request, make_response
from sqlalchemy.orm import joinedload
from flask.json import jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from modelos import db

class BistaLogin(Resource):
    pass


class VistaSignUp(Resource):
    pass


class VistaTasks(Resource):
    pass