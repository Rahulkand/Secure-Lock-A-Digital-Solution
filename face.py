import cv2
import pickle
import face_recognition
import numpy as np
import cvzone
from DB import DataBaseConnection as dbc
from DB import fectchuserdata as fetch
from DB import  userdataTodatabase as udtdb

counter = 0
flag_fa = 0
flag_fi = 0
id = -1
def face_recognization():
    vcap = cv2.VideoCapture(1)
    vcap.set(3,1280)
    vcap.set(4,720)

    # dbc.getConnection()
    print("Extracting the 128 measurements from file...")
    file = open("encode128.p","rb")
    encoded_faces_list_with_ids = pickle.load(file)
    file.close()
    print("Extraction Done...")
    encoded_face_list,user_ids = encoded_faces_list_with_ids

    while True:
        success, image = vcap.read()
        imgS = cv2.resize(image,(0,0),None,0.25,0.25)
        imgS = cv2.cvtColor(imgS,cv2.COLOR_BGR2RGB)

        face_currfrm_loc = face_recognition.face_locations(imgS)
        encode_currfrm_face = face_recognition.face_encodings(imgS,face_currfrm_loc)

        for encode_face_measurement,face_loc in zip(encode_currfrm_face,face_currfrm_loc):
            matchs = face_recognition.compare_faces(encoded_face_list,encode_face_measurement)
            face_dis = face_recognition.face_distance(encoded_face_list,encode_face_measurement)
            match_ind = np.argmin(face_dis)
            if matchs[match_ind]:
                global counter,flag_fa,id
                id = user_ids[match_ind]
                if counter==0:
                    counter =  1
                    flag_fa = 1
                # Draw bounding box around the face
                top, right, bottom, left = face_loc
                # Since we resized the image by 0.25
                top *= 4 
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
        if counter!=0:
            if counter==1:
                print(fetch.fetch_data(id))
                print(flag_fa)
            counter+=1
        ret,buffer = cv2.imencode('.jpg',image)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        # cv2.imshow("FACE",imgS)
        # cv2.waitKey(1)
       

# face_recognization()
