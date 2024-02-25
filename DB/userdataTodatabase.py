
from DB import DataBaseConnection as dbc

def addUsers(user):
    ref = dbc.db.reference("users")
    for key,val in user.items():
        ref.child(key).set(val)