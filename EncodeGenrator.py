import cv2 
import face_recognition
import pickle
import os

folderPath="images/"
mode_path = os.listdir(folderPath)
user_ids = []
images_list = []

for path in mode_path:
    images_list.append(cv2.imread(os.path.join(folderPath,path)))
    user_ids.append(os.path.splitext(path)[0])

encoded_faces_list = []
def encodeFaces():
    for img in images_list:
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        face_loc = face_recognition.face_locations(img)
        encoded_face = face_recognition.face_encodings(img,face_loc)[0]
        encoded_faces_list.append(encoded_face)

print("Encoding Started...")
encodeFaces()
print("Encoding Finished...")

encoded_faces_list_with_ids = [encoded_faces_list,user_ids]

print("Saving the measurements to the file...")
file = open("encode128.p","wb")
pickle.dump(encoded_faces_list_with_ids,file)
file.close()
print("File Saved...")