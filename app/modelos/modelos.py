from flask_sqlalchemy import SQLAlchemy
from enum import Enum
from marshmallow import fields, Schema
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

db = SQLAlchemy()

class DocumentFormat(Enum):
    mp4 = 'mp4'
    webm = 'webm'
    avi = 'avi'
    mpeg = 'mpeg'
    wmv = 'wmv'

class DocumentStatus(Enum):
    InQueue = 'InQueue'
    InProgress = 'InProgress'
    Ready = 'Ready'
    Error = 'Error'

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user = db.Column(db.String(512))
    email = db.Column(db.String(512), unique=True, nullable=False)
    password = db.Column(db.String(512))
    documents = db.relationship('Document', backref='user', lazy=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    filename = db.Column(db.String(512),  nullable=False)
    timestamp = db.Column(db.String(512),  nullable=False)
    status = db.Column(db.Enum(DocumentStatus), nullable=False)
    format_in = db.Column(db.Enum(DocumentFormat), nullable=False)
    format_out = db.Column(db.Enum(DocumentFormat), nullable=False)
    location_in = db.Column(db.String(512),  nullable=False)
    file_in = db.Column(db.LargeBinary, nullable=True)
    file_out = db.Column(db.LargeBinary, nullable=True)

    def __str__(self) -> str:
        return super().__str__()

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_relationships = True
        load_instance = True

    id = fields.String()  