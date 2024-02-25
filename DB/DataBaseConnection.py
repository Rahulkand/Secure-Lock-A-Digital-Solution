import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
def getConnection():
    cred = credentials.Certificate("DB/securelockdatabaseaccesskey.json")
    firebase_admin.initialize_app(cred,{
        "databaseURL":"https://lockdb-e106f-default-rtdb.firebaseio.com/",
        "storageBucket":"lockdb-e106f.appspot.com"
    })
    return cred