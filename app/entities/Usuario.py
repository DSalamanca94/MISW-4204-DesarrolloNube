class Usuario():
    def __init__(self, id, username, useremail, userpassword):
        self.id = id
        self.username = username
        self.useremail = useremail
        self.userpassword = userpassword

    def to_JSON(self):
        return {
            'id':self.id,
            'username':self.username,
            'useremail':self.useremail,
            'userpassword':self.userpassword
        }