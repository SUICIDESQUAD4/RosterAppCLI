#app/controllers/initialize.py
from .user import create_user
from App.database import db


def initialize():
    db.drop_all()
    db.create_all()
    create_user('bob', 'bobpass', 'admin')
    create_user('jane', 'janepass', 'staff')
    create_user('alice', 'alicepass', 'staff')
    create_user('tim', 'timpass', 'user')