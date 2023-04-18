from csv import reader
from datetime import datetime
import os
import uuid
import cv2
import certifi
import ssl
import numpy as np
from flask import Flask, jsonify, make_response, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_cors import CORS
import numpy
from models import Alert, db, bcrypt, User, Address, Meter, Reading
from flask_swagger_ui import get_swaggerui_blueprint
import easyocr
from deeplearning import OCR
# import pytesseract
# import textract
from PIL import Image, ImageFilter, ImageOps

app = Flask(__name__)
# CORS(app, origins=["http://localhost:8081"])
cors = CORS(app, resources={r"/*": {"origins": "*"}},
            supports_credentials=True)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:''@localhost/aut_python'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://test:test@192.168.99.245:5432/tester'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://test:test@192.168.99.245:5432/version02042023'
app.config['JWT_SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER_ALERTS'] = './photos'
app.config['UPLOAD_FOLDER_METERS'] = './meter_photos'
db.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)


@app.before_first_request
def create_tables():
    db.create_all()


### swagger specific ###
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "auth-backend-python"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
### end swagger specific ###


@app.route('/')
def index():
    return 'Hello, world!'


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    egn_hash = data.get('egn_hash')
    addresses = data.get('addresses')
    client_number = data.get('client_number')

    if not client_number or not name or not email or not egn_hash:
        return jsonify({'message': 'Missing required information'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists'}), 400

    if User.query.filter_by(egn_hash=egn_hash).first():
        return jsonify({'message': 'User with EGN already exists'}), 400

    # Create new user and address objects
    user = User(client_number=client_number, name=name,
                email=email, egn_hash=egn_hash)
    for address in addresses:
        addr = Address(user_id=client_number, address=address["address"])
        db.session.add(addr)

    # Add user and address to database
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201


@app.route('/api/login', methods=['POST'])
# returns access token as header
def login():
    data = request.json
    user = User.query.filter_by(client_number=data['client_number']).first()
    if not user or not user.check_egn_hash(data['egn_hash']):
        return jsonify({'message': 'Invalid credentials'}), 401
    access_token = create_access_token(identity=user.client_number)
    resp = make_response(jsonify({'message': 'Successfully logged in'}), 200)
    return jsonify({'access_token': access_token}), 200
# returns access token as cookie
# def login():
#     data = request.json
#     user = User.query.filter_by(email=data['email']).first()
#     if not user or not user.check_password(data['password']):
#         return jsonify({'message': 'Invalid credentials'}), 401
#     access_token = create_access_token(identity=user.id)toir
#     resp = make_response(jsonify({'message': 'Successfully logged in'}), 200)
#     resp.set_cookie('access_token', access_token, httponly=True)
#     return resp


@app.route('/api/user', methods=['GET'])
@jwt_required()
def user():
    client_number = get_jwt_identity()
    user = User.query.filter_by(client_number=client_number).first()
    return jsonify({'name': user.name, 'email': user.email}), 200


@app.route('/api/user/addresses', methods=['GET'])
@jwt_required()
def user_info_addresses():
    client_number = get_jwt_identity()
    user = User.query.filter_by(client_number=client_number).first()
    addresses = [address.address for address in user.addresses]
    return jsonify({'name': user.name, 'email': user.email, 'addresses': addresses}), 200


# test for the get all info route
@app.route('/api/users/total', methods=['GET'])
@jwt_required()
def get_all_users_info():
    client_number = get_jwt_identity()
    user = User.query.filter_by(client_number=client_number).first()
    user_dict = {
        'name': user.name,
        'email': user.email,
        'egn_hash': user.egn_hash,
        'created_at': user.created_at,
        'updated_at': user.updated_at,
        'client_number': user.client_number,
        'addresses': []
    }
    for address in user.addresses:
        address_dict = {
            'id': address.id,
            'user_id': address.user_id,
            'address': address.address,
            'meter_readings': []
        }
        for meter in address.meter_readings:
            meter_dict = {

                'meter_number': meter.meter_number,
                'address_id': meter.address_id,
                'installation_date': meter.installation_date,
                'photo': meter.photo,
                'readings': []
            }
            # for reading in meter.readings:
            #     reading_dict = {
            #         'id': reading.id,
            #         'meter_id': reading.meter_id,
            #         'reading_date': reading.reading_date,
            #         'reading_value': reading.reading_value
            #     }
            #     meter_dict['readings'].append(reading_dict)
            address_dict['meter_readings'].append(meter_dict)
        user_dict['addresses'].append(address_dict)
    return jsonify(user_dict)
# def get_all_users_info():
#     client_number = get_jwt_identity()
#     user = User.query.filter_by(client_number=client_number).first()
#     user_dict = {
#         'name': user.name,
#         'email': user.email,

#         'created_at': user.created_at,
#         'updated_at': user.updated_at,
#         'client_number': user.client_number,
#         'addresses': [],
#         'meter_readings': [],
#         'readings': []
#     }
#     for address in user.addresses:
#         address_dict = {
#             'id': address.id,
#             'user_id': address.user_id,
#             'address': address.address,

#         }
#         user_dict['addresses'].append(address_dict)
#         for meter in address.meter_readings:
#             meter_dict = {
#                 'id': meter.id,
#                 'meter_number': meter.meter_number,
#                 'address_id': meter.address_id,
#                 'installation_date': meter.installation_date,

#             }
#             user_dict['meter_readings'].append(meter_dict)
#             for reading in meter.readings:
#                 reading_dict = {
#                     'id': reading.id,
#                     'meter_id': reading.meter_id,
#                     'reading_date': reading.reading_date,
#                     'reading_value': reading.reading_value
#                 }
#                 user_dict['readings'].append(reading_dict)

#     return jsonify(user_dict)


# @app.route('/api/user/addReadings', methods=['POST'])
# def add_readings():
#     data = request.get_json()
#     readings = data['readings']
#     for reading in readings:
#         new_reading = Reading(meter_number=reading['meter_number'],
#                               reading_date=datetime.now().date(),
#                               reading_value=reading['readings'])
#         db.session.add(new_reading)
#     db.session.commit()
#     return jsonify({'message': 'New reading added successfully.'}), 201

@app.route('/api/user/addReadings', methods=['POST'])
def add_readings():
    data = request.get_json()
    # if 'readings' not in data:
    #    return jsonify({'message': 'No readings data provided.'}), 400

    for reading in data:

        new_reading = Reading(
            meter_number=reading['meter_number'],
            reading_date=datetime.now().date(),
            reading_value=reading['readings'])
        db.session.add(new_reading)
        db.session.commit()
    return jsonify({'message': 'New reading added successfully.'}), 201


@app.route('/api/report-alert', methods=['POST'])
def report_alert():
    alert_data = request.form.to_dict()
    photo = request.files['photo']
    unique_filename = f"{uuid.uuid4().hex}.jpg"  # create a unique filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER_ALERTS'], unique_filename)
    photo.save(filepath)
    alert = Alert(
        alert_description=alert_data['alert_description'],
        alert_location_description=alert_data['alert_location_description'],
        photo=filepath,
        latitude=float(alert_data['latitude']),
        longitude=float(alert_data['longitude'])
    )
    db.session.add(alert)
    db.session.commit()
    return jsonify({'message': 'Alert created successfully.'}), 201

reader = easyocr.Reader(['en'])


@app.route('/ocr', methods=['POST'])
def ocr():
    # check if request contains a file
 if 'file' not in request.files:
    return jsonify({'error': 'no file provided'})

 file = request.files['file']

# check if file has an allowed extension
 allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
 if file.filename.split('.')[-1].lower() not in allowed_extensions:
    return jsonify({'error': 'invalid file extension'})

# read image from file
 image = cv2.imdecode(numpy.frombuffer(
    file.read(), numpy.uint8), cv2.IMREAD_UNCHANGED)

# preprocess image
 image = cv2.resize(image, None, fx=0.5, fy=0.5,
                   interpolation=cv2.INTER_AREA)  # rescale image
 gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # convert to grayscale
 edges = cv2.Canny(image, 100, 200)
 blur = cv2.GaussianBlur(gray, (5, 5), 0)  # apply Gaussian Blur
 _, thresh = cv2.threshold(
        blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # apply thresholding

# read text from preprocessed image using EasyOCR
 results = reader.readtext(edges)

# extract text from results and concatenate into a string
 text = ' '.join([result[1] for result in results])

 return jsonify({'text': text})
    # # check if request contains a file
    # if 'file' not in request.files:
    #     return jsonify({'error': 'no file provided'})

    # file = request.files['file']

    # # check if file has an allowed extension
    # allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
    # if file.filename.split('.')[-1].lower() not in allowed_extensions:
    #     return jsonify({'error': 'invalid file extension'})

    # # read text from preprocessed image using textract
    # text = textract.process(file, method='tesseract', language='eng')

    # # convert bytes to string
    # text = text.decode('utf-8')

    # return jsonify({'text': text})




    # # check if request contains a file
    # if 'file' not in request.files:
    #     return jsonify({'error': 'no file provided'})

    # file = request.files['file']

    # # check if file has an allowed extension
    # allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
    # if file.filename.split('.')[-1].lower() not in allowed_extensions:
    #     return jsonify({'error': 'invalid file extension'})

    # # read image from file
    # image = Image.open(file)

    # # preprocess image
    # # image = image.resize((int(image.width/2), int(image.height/2)),
    # #                      resample=Image.LANCZOS)  # rescale image
    # gray = image.convert('L')  # convert to grayscale
    # # blur = gray.filter(ImageFilter.GaussianBlur(
    # #     radius=5))  # apply Gaussian Blur
    # # thresh = ImageOps.autocontrast(blur)  # apply automatic contrast adjustment

    # # read text from preprocessed image using Tesseract OCR
    # tess = pytesseract.image_to_string(gray)

    # return jsonify({'text': tess})

# Define an endpoint for your Flask API that will receive the image to be processed.
@app.route('/detect_objects', methods=['POST'])
def detect_objects():
    alert_data = request.form.to_dict()
    photo = request.files['photo_0']
    unique_filename = f"{uuid.uuid4().hex}.jpg"  # create a unique filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER_METERS'], unique_filename)
    photo.save(filepath)
    print(filepath + unique_filename)
    response = OCR(unique_filename,filepath)
    return jsonify(response)
   


if __name__ == '__main__':
    app.run(debug=True)

