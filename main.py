from flask import Flask, render_template, request, jsonify, redirect, url_for, Response,session
import pyotp
import firebase_admin
from base64 import b64encode
import hashlib
from DB import DataBaseConnection as dbc
from DB import fectchuserdata as fd
import cv2
import pickle
import numpy as np
import face
import os
import requests
from gpiozero import Servo, LED
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
from twilio.rest import Client
RASPBERRY_PI_IP = "192.168.137.58"

acc_id = 202306

face_acc_done=0

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hello'

# Initialize Firebase Admin SDK
print("Establishing Database Connection")
access = dbc.getConnection()
print("Connection Established Successfully to SecureLock DB")
print("Establishing network...")
account_sid = 'ACbc4944262a6ccca161f8c3c90ddea0c7'
auth_token = '91850baa77f92658fe5fa48e8c59d031'
twilio_phone_number = '+14122754854'
client = Client(account_sid,auth_token)
print("Network Established...")
otp_ref = dbc.db.reference('otp')

# Dictionary to store OTPs, map phone numbers to emails
otp_storage = {}

def generate_otp():
    # Generate a 6-digit OTP
    return str(pyotp.TOTP(pyotp.random_base32()).now())

@app.route('/')
def home():
    #print(id+str(counter))
    return render_template('index.html')
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        global acc_id
        print(acc_id)
        acc_id = acc_id + 1
        print(acc_id)
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        # Check if the post request has the file part
        strid = str(acc_id)
        print(strid)
        #counter variable for id
        #Store user data in Realtime Database
        users_ref = dbc.db.reference('usersnew')
        users_ref.child(strid).set({
            'name': name,
            'email': email,
            'phone': phone,
            'password': password
        })
        
        return redirect(url_for('login'))

    return render_template('register.html')

    # return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        user_ref = None

        # Check if the identifier is an email or a phone number
        if '@' in identifier:
            user_ref = dbc.db.reference('usersnew').order_by_child('email').equal_to(identifier).get()
        else:
            user_ref = dbc.db.reference('usersnew').order_by_child('phone').equal_to(identifier).get()

        if user_ref:
            user_data = list(user_ref.values())[0]
            email = user_data['email']
            phone = user_data['phone']
            stored_password = user_data['password']
            print(user_data)
            print(f"Fetched Password: {stored_password}")
            print(f"Entered Password: {password}")

            # Verify the password
            if verify_password(password, stored_password):
                # Generate and store OTP in the Firebase Realtime Database
                otp = generate_otp()
                otp_ref.child(identifier).set(otp)
                user_phone_number = "+91" + phone
                message = client.messages.create(
                    body=f'Your OTP for mobile verification is: {otp}',
                    from_=twilio_phone_number,
                    to=user_phone_number)
                # Send OTP to user (you may use SMS or email for this step)

                return render_template('otp.html', identifier=identifier)
            else:
                return render_template('login.html', error='Incorrect password')
        else:
            return render_template('login.html', error='User not found')

    return render_template('login.html', error=None)

# Function to verify hashed password
def verify_password(entered_password, stored_password):
    return entered_password == stored_password


@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    if 'user_name' in session and 'user_phone' in session:
        user_name = session['user_name']
        user_phone = session['user_phone']
        face_done = session['face_recognized']
        if request.method == 'POST':
            # Handle form submission from camera feed page (if needed)
            # For example, you may want to process the form data submitted from the camera feed page
            # and update the session data accordingly.
            pass

        return render_template('dashboard.html', user_name=user_name, user_phone=user_phone, face_toggle=session.get('face_recognized', False),fingerprint_toggle=session.get('fingerPrint_recognized',False),otp_toggle=session.get('otp_done',False),unique_id=session.get('unique_id'))
    else:
        # Redirect to the login page if the user is not logged in
        return redirect(url_for('login'))

@app.route('/otp_verification',methods=['GET','POST'])
def otp_verification():
    
    user_otp = request.form.get('otp')
    # Retrieve stored OTP from the Firebase Realtime Database
    stored_otp_ref = dbc.db.reference('otp').child(session['user_phone'])
    stored_otp = stored_otp_ref.get()

    if stored_otp and user_otp == stored_otp:
        # Clear the OTP from the database after successful verification
        stored_otp_ref.delete()
        session['otp_done'] = True
        user_name = session['user_name']
        user_phone= session['user_phone']
        return render_template('dashboard.html', user_name=user_name, user_phone=user_phone, face_toggle=session.get('face_recognized', False),fingerprint_toggle=session.get('fingerPrint_recognized',False),otp_toggle=session.get('otp_done',False),unique_id=session.get('unique_id'))
    else:
        return render_template('lock_otp.html',error="Invalid OTP")

@app.route('/otp_lock_open',methods=['GET','POST'])
def otp_lock_open():
        
        return render_template('lock_otp.html')


@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    identifier = request.form.get('identifier')
    user_otp = request.form.get('otp')
    session['identifier'] = identifier
    # Retrieve stored OTP from the Firebase Realtime Database
    stored_otp_ref = dbc.db.reference('otp').child(identifier)
    stored_otp = stored_otp_ref.get()

    if stored_otp and user_otp == stored_otp:
        # Clear the OTP from the database after successful verification
        stored_otp_ref.delete()
        user_ref = dbc.db.reference('usersnew').order_by_child('phone').equal_to(identifier).get()
        if user_ref:
            user_data = list(user_ref.values())[0]
            user_name = user_data.get('name', '')
            user_phone = user_data.get('phone', '')
            session['user_name'] = user_name
            session['user_phone'] = user_phone
            session['face_recognized'] = False
            session['otp_done'] = False
            session['fingerPrint_recognized'] = False
            return redirect(url_for('dashboard'))
        # return render_template('facerecognition.html')
        else:
            return render_template('login.html', error='User not found')
    else:
        return render_template('otp.html', identifier=identifier, error='Invalid OTP')

# @app.route("/lock",methods = ['GET',"POST"])
# def lock():
#     session['otp_done'] = False
#     session['face_recognized'] = False
#     session['fingerPrint_recognized'] = False
#     user_name = session['user_name']
#     user_phone = session['user_phone']
#     return render_template('dashboard.html', user_name=user_name, user_phone=user_phone, face_toggle=session.get('face_recognized', False),fingerprint_toggle=session.get('fingerPrint_recognized',False),otp_toggle=session.get('otp_done',False))

@app.route("/lock",methods = ['GET',"POST"])
def lock():
    session['otp_done'] = False
    session['face_recognized'] = False
    session['fingerPrint_recognized'] = False
    requests.get(f"http://{RASPBERRY_PI_IP}:5000/lockback")
    user_name = session['user_name']
    user_phone = session['user_phone']
    return render_template('dashboard.html', user_name=user_name, user_phone=user_phone, face_toggle=session.get('face_recognized', False),fingerprint_toggle=session.get('fingerPrint_recognized',False),otp_toggle=session.get('otp_done',False))

@app.route('/verification_face',methods=['GET','POST'])
def verification_face():
    temp_id = face.id
    session['unique_id'] = temp_id
    user_face_id = dbc.db.reference('users').child(str(temp_id)).get()
    phone_num = user_face_id['phone']
    # acc_ref = dbc.db.reference('usersnew').child(str(temp_id)).get()
    # print(acc_ref)
    # acc_phone = acc_ref['phone']
    # print(type(acc_phone),type(phone_num))
    temp_phone = session['user_phone']
    if(str(temp_phone) == str(phone_num)):
        global face_acc_done,enable_biometric_toggle
        face_acc_done = 1
        session['face_recognized'] = True
        otp = generate_otp()
        otp_ref.child(session['user_phone']).set(otp)
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html')

@app.route('/face_recognition', methods=['GET', 'POST'])
def face_recognition():
    if request.method == 'POST':
        return render_template('camera.html')
    

@app.route('/video_feed')
def video_feed():
    return Response(face.face_recognization(), mimetype='multipart/x-mixed-replace; boundary=frame')

def search_finger():
    try:
        response = requests.post(f"http://{RASPBERRY_PI_IP}:5000/search")
        result = response.json()

        return result
    except requests.exceptions.RequestException as e:
        return {'error': f'Error connecting to the Raspberry Pi: {e}'}
        
    
@app.route('/verify_fingerprint', methods=['POST'])
def verify_fingerprint():
    fingerprint_data = request.form.get('fingerprint_data')

    # Simulate fingerprint verification
    if fingerprint_data == "CapturedFingerprintData":
        # Call the search_finger function to communicate with Raspberry Pi
        search_result = search_finger()
        print(search_result)
        pos = search_result['message']

        if (str(pos) =='No match found!'):
            #return f"Error: {search_result['error']}"
            return render_template('finger.html')
        
        
        print(pos)
        pos = int(pos)
        if(pos>=0):
            finger_ref = dbc.db.reference('fingerprints').child(str(pos)).get()
            phone_numfin = finger_ref['phone']
            print(phone_numfin)
            print(session['user_phone'])
            if(str(phone_numfin) == str(session['user_phone'])):
                print("verified")
                session['fingerPrint_recognized'] = True
                otp = generate_otp()
                otp_ref.child(session['user_phone']).set(otp)
                # Send OTP to user (you may use SMS or email for this step)
                user_phone_number = "+91" + str(session['user_phone'])
                message = client.messages.create(
                    body=f'Your OTP for locker verification is: {otp}',
                    from_=twilio_phone_number,
                    to=user_phone_number
                )

                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html')

    else:
        return "Fingerprint verification failed"
    
@app.route('/trigger_servo', methods=['GET'])
def trigger_servo():
    try:
        response = requests.get(f"http://{RASPBERRY_PI_IP}:5000/servo")
        result = response.json()

        return redirect(url_for('dashboard'))
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Error connecting to the Raspberry Pi: {e}'})

@app.route('/finger_recog', methods=['GET', 'POST'])
def finger_recog():
        return render_template('finger.html')

@app.route("/logout",methods=["GET","POST"])
def logout():
    return render_template("index.html")
if __name__ == '__main__':
    app.run(debug=True)
