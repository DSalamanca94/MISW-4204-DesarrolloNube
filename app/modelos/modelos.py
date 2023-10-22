from flask_sqlalchemy import SQLAlchemy
from enum import Enum

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
    email = db.Column(db.String(512))
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

