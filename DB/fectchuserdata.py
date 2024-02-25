from DB import DataBaseConnection as dbc
def fetch_data(user_id):
    user_info = dbc.db.reference(f"users/{user_id}").get()
    return user_info