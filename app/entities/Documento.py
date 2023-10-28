from enum import Enum

class Documento():
    def __init__(self,id,user_id=None,filename=None,timestamp=None,status=None,format_in=None,format_out=None,location_in=None,location_out=None) -> None:
        self.id = id
        self.user_id = user_id
        self.filename = filename
        self.timestamp = timestamp
        self.status = status
        self.format_in = format_in
        self.format_out = format_out
        self.location_in = location_in
        self.location_out = location_out

    def to_JSON(self):
        return {
            'id':self.id,
            'user_id':self.user_id,
            'filename':self.filename,
            'timestamp':self.timestamp,
            'status':self.status,
            'format_in':self.format_in,
            'format_out':self.format_out,
            'location_in':self.location_in,
            'location_out':self.location_out
        }
    
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