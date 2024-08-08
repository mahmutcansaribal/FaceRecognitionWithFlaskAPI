from flask import Flask, render_template, request, jsonify
import cv2
import face_recognition
import os
import base64
import sqlite3
from io import BytesIO
from PIL import Image
import numpy as np
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db_path = 'landMarks.db'

# Yüz kodlama ve veritabanına kaydetme fonksiyonları
def encode_faces(image):
    try:
        encodings = face_recognition.face_encodings(image)
        return encodings[0] if encodings else None
    except Exception as e:
        print(f"Error encoding faces: {e}")
        return None

def save_encoding_and_landmarks_to_db(user_id, encoding, landmarks):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS face_data
                            (user_id TEXT, encoding BLOB, chin TEXT, left_eyebrow TEXT, right_eyebrow TEXT, 
                            nose_bridge TEXT, nose_tip TEXT, left_eye TEXT, right_eye TEXT, 
                            top_lip TEXT, bottom_lip TEXT)''')
            cursor.execute('''INSERT INTO face_data 
                            (user_id, encoding, chin, left_eyebrow, right_eyebrow, nose_bridge, nose_tip, 
                            left_eye, right_eye, top_lip, bottom_lip) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                        (user_id,
                            encoding.tobytes(),
                            json.dumps(landmarks.get('chin', [])),
                            json.dumps(landmarks.get('left_eyebrow', [])),
                            json.dumps(landmarks.get('right_eyebrow', [])),
                            json.dumps(landmarks.get('nose_bridge', [])),
                            json.dumps(landmarks.get('nose_tip', [])),
                            json.dumps(landmarks.get('left_eye', [])),
                            json.dumps(landmarks.get('right_eye', [])),
                            json.dumps(landmarks.get('top_lip', [])),
                            json.dumps(landmarks.get('bottom_lip', []))))
            print("Veriler veri tabanına kaydedildi!")
            conn.commit()
            conn.close()
        print("VERİ TABANINA EKLENDİ")
    except Exception as e:
        print(f"Error saving to database: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tespitEt',methods=['GET'])
def tespitEt():
    return render_template('TespitEt.html')

@app.route('/api/kullaniciEkle', methods=['POST'])
def kullaniciEkle():
    data = request.get_json()
    kAdi = data.get('ad')
    kSadi = data.get('soyad')
    face_image = data.get('face_image')

    # Base64 formatındaki görüntüyü decode et
    image_data = base64.b64decode(face_image.split(',')[1])
    image = Image.open(BytesIO(image_data))
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    encoding = encode_faces(image)
    landmarks = face_recognition.face_landmarks(image)

    if encoding is not None and landmarks:
        user_id = f"{kAdi} {kSadi}"
        save_encoding_and_landmarks_to_db(user_id, encoding, landmarks[0])
        return jsonify({'success': 'Fotoğraf Encodlandi ve veri tabanına kaydedildi'})
    else:
        return jsonify({'error': 'Fotoğraf Encodlanamadi'})

def calculate_chin_distance(chin1, chin2):
        chin1 = np.array(chin1)
        chin2 = np.array(chin2)
        return np.sqrt(np.sum((chin1 - chin2) ** 2))
def calculate_left_eye_distance(eyeleft1,eyeleft2):
    eyeleft1 = np.array(eyeleft1)
    eyeleft2 = np.array(eyeleft2)
    return np.sqrt(np.sum((eyeleft1 - eyeleft2) ** 2))
def calculate_right_eye_distance(eyeright1, eyeright2):
    eyeright1 = np.array(eyeright1)
    eyeright2 = np.array(eyeright2)
    return np.sqrt(np.sum((eyeright1 - eyeright2) ** 2))
def calculate_top_lib_distance(toplip1,toplip2):
    toplip1 = np.array(toplip1)
    toplip2 = np.array(toplip2)
    return np.sqrt(np.sum((toplip1-toplip2)))
def calculate_bottom_lib_distance(bottomlip1,bottomlip2):
    bottomlip1 = np.array(bottomlip1)
    bottomlip2 = np.array(bottomlip2)
    return np.sqrt(np.sum((bottomlip1-bottomlip2)))

def parse_chin_data(chin_blob):
    return json.loads(chin_blob)
def parse_left_eye(eye_left):
    return json.loads(eye_left)
def parse_right_eye(eye_right):
    return json.loads(eye_right)
def parse_top_lib(top_lib):
    return json.loads(top_lib)
def parse_bottom_lib(bottom_lib):
    return json.loads(bottom_lib)
# Veritabanından yüz verilerini alma ve karşılaştırma
def get_face_data_from_db(encoding, landmarks):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, encoding, chin, left_eyebrow, right_eyebrow, nose_bridge, nose_tip, left_eye, right_eye, top_lip, bottom_lip
        FROM face_data
    ''')
    rows = cursor.fetchall()
    conn.close()

    best_match_user_id = None
    min_chin_distance = float('inf')
    min_left_eye_distance = float('inf')
    min_right_eye_distance = float('inf')
    min_top_lip_distance = float('inf')
    min_bottom_lip_distance = float('inf')
#ROS Entegrasyonu
    for row in rows:
        user_id = row[0]
        encoding_blob = row[1]
        chin_blob = row[2]
        leftEyeBlob = row[7]
        rightEyeBlob = row[8]
        topLibBlob = row[9]
        bottomLibBlob = row[10]

        known_encoding = np.frombuffer(encoding_blob, dtype=np.float64)

        encoding_match = face_recognition.compare_faces([known_encoding], encoding, tolerance=0.57)
        
        chin_coordinates = parse_chin_data(chin_blob)
        left_eye_coordinates = parse_left_eye(leftEyeBlob)
        right_eye_coordinates = parse_right_eye(rightEyeBlob)
        top_lib_coordinates = parse_top_lib(topLibBlob)
        bottom_lib_coordinates = parse_bottom_lib(bottomLibBlob)

        '''
        YAPILAN DEGİSİKLİKLER 
        1- HER BİR LANDMARKS VE ENCODING DEGERİ  İÇİN LANDMARKS[0] KALDIRILDI
        2- IF YAPISI DÜZENLENDİ
        '''
        if 'chin' in landmarks and 'left_eye' in landmarks and 'right_eye' in landmarks and 'top_lip' in landmarks and 'bottom_lip' in landmarks :
            chin_distance = calculate_chin_distance(chin_coordinates, landmarks['chin'])
            left_eye_distance = calculate_left_eye_distance(left_eye_coordinates,landmarks['left_eye'])
            right_eye_distance = calculate_right_eye_distance(right_eye_coordinates,landmarks['right_eye'])
            top_lib_distance = calculate_top_lib_distance(top_lib_coordinates,landmarks['top_lip'])
            bottom_lib_distance = calculate_bottom_lib_distance(bottom_lib_coordinates,landmarks['bottom_lip'])
            # print(f"Chin Distance : {chin_distance}")
            # print(f"Left Eye Distance : {left_eye_distance}")
            # print(f"Right Eye Distance : {right_eye_distance}")
            # print(f"top lib Distance : {top_lib_distance}")
            # print(f"bottom lib Distance : {bottom_lib_distance}")

            if encoding_match[0] and chin_distance < min_chin_distance and left_eye_distance < min_left_eye_distance and right_eye_distance < min_right_eye_distance and top_lib_distance < min_top_lip_distance and bottom_lib_distance < min_bottom_lip_distance:
                best_match_user_id = user_id
                min_chin_distance = chin_distance
                min_left_eye_distance = left_eye_distance
                min_right_eye_distance = right_eye_distance
                min_top_lip_distance = top_lib_distance
                min_bottom_lip_distance = bottom_lib_distance
                print(f"KULLANICI  :{best_match_user_id}")
    return best_match_user_id
@app.route('/api/tespitEt', methods=['POST'])
def tespit_et():
    data = request.json
    frame_data = data['frame'].split(',')[1]
    frame = np.frombuffer(base64.b64decode(frame_data), np.uint8)
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

    face_locations = face_recognition.face_locations(frame, model="hog")
    if face_locations:
        face_landmarks = face_recognition.face_landmarks(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        if face_landmarks and face_encodings:

            result = []
            for (faceler, encoding, landmarks) in zip(face_locations, face_encodings, face_landmarks):
                top, right, bottom, left = faceler
                user_id = get_face_data_from_db(encoding, landmarks)
                print(f"user_id {user_id}")
                cv2.putText(frame, user_id, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                result.append({
                    'user_id': user_id,
                    'box': (left, top, right, bottom)
                })
            return jsonify({'result': result})
    return jsonify({'result': []})  # Yüz tespit edilmediyse boş sonuç döndür

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)

