from flask_sqlalchemy import SQLAlchemy
from enum import Enum

db = SQLAlchemy()

class DocumentFormat(Enum):
    MP4 = 'MP4'
    WEBM = 'WEBM'
    AVI = 'AVI'
    MPEG = 'MPEG'
    WMV = 'WMV'

class DocumentStatus(Enum):
    InQueue = 'InQueue'
    InProgress = 'InProgress'
    Ready = 'Ready'

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(512))
    password = db.Column(db.String(512))
    documents = db.relationship('Document', backref='user', lazy=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.Enum(DocumentStatus), nullable=False)
    format_in = db.Column(db.Enum(DocumentFormat), nullable=False)
    format_out = db.Column(db.Enum(DocumentFormat), nullable=False)
    file_in = db.Column(db.LargeBinary, nullable=False)
    file_out = db.Column(db.LargeBinary, nullable=True)