from DB import DataBaseConnection as dbc
import os
folderPath="Images"
mode_path = os.listdir(folderPath)

for path in mode_path:
    filename = f"{folderPath}/{path}"

    bucket = dbc.storage.bucket()
    blob = bucket.blob(filename)
    blob.upload_from_filename(filename)