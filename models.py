from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, first_name, last_name, email, password, role, profile_img=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.role = role
        self.profile_img = profile_img
