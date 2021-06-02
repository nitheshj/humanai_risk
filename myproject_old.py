"""
This script contains the functions necessary for the complex operations that can't be performed in Game Scriptor
@author: Nithesh Javvaji
@date: 08-18-2020
@project: Tier-1 Human AI Collaboration

"""
# from datetime import timedelta
import uuid
# import jwt
from flask import Flask, request, send_from_directory, session
from flask_session import Session
from database import Database
import configparser
# import math
import random
import os
from flask_cors import CORS

PATH = os.path.join(os.path.abspath('..'), 'Tier1/client/')

app = Flask(__name__, static_url_path="", static_folder=PATH)
CORS(app, resources={r"/*": {"origins": "https://studycrafter.com"}}, supports_credentials=True,
     allow_headers=["Origin", "X-Requested-With", "Content-Type", "Accept", "x-auth"])
SESSION_TYPE = 'filesystem'
SESSION_PERMANENT = False  # Session cookie will expire when browser is closed
app.secret_key = 'human_ai'
app.config.from_object(__name__)
Session(app)

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')


# To make the session cookie expire after 5 Minutes of closing browser
# @app.before_request
# def make_session_permanent():
#     session.permanent = True
#     app.permanent_session_lifetime = timedelta(minutes=5)


# @app.after_request
# def after_request(response):
#     """ after_request """
#
#     response.headers.add('Access-Control-Allow-Origin', 'https://studycrafter.com')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
#     return response


@app.route('/set/')
def start():
    session['user_id'] = str(uuid.uuid4())
    session['sequence'] = random.sample(range(1, 200), 199)
    session['attention'] = [570, 539, 617, 653, 684, 725, 749, 771, 806, 812]
    return session['user_id']


@app.route('/get/')
def get():
    return session.get('user_id', 'not set')


@app.route('/api/nextid', methods=['GET'])
def nextid():
    """
    This function randomly chooses an ID from IDs List
    :return
    """
    attention = int(request.args.get('att'))
    seq = session.get('sequence', None)
    new_choice = random.choice(seq)

    if attention == 0:
        seq.remove(new_choice)
        session['sequence'] = seq

    # print(new_choice)

    return str(new_choice)


@app.route('/api/getfico', methods=['GET'])
def getfico():
    """
    This function randomly chooses an ID from IDs List
    :return
    """
    attention = int(request.args.get('att'))
    att_seq = session.get('attention', None)
    fico = random.choice(att_seq)

    if attention != 0:
        att_seq.remove(fico)
        session['attention'] = att_seq

    # print(fico)

    return str(fico)


@app.route('/api/getcredit', methods=['GET'])
def getcredit():
    image_id = int(request.args.get('image_id'))

    db = Database(config)

    # T1 =199, T2 = 202, C = 196
    credit = db.query_database("""SELECT test.Credit_rating FROM test  
                                    WHERE TreatID = %s AND Treatment = %s""", (image_id, "T1",))
    # print(type(credit))
    # print(credit)
    return str(credit[0])


def write_file(data, filename):
    """

    :param data:
    :param filename:
    :return:
    """
    # Convert binary data to proper format and write it on Hard Disk
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'wb+') as file:
        file.write(data[0])


@app.route('/api/getimage', methods=['GET'])
def getimage():
    image_id = int(request.args.get('image_id'))
    name = str(request.args.get('name'))
    attention = int(request.args.get('att'))
    user_id = session.get('user_id', None)

    treatment = "T1" if attention == 0 else "C"

    db = Database(config)

    # T1 =199, T2 = 202, C = 196
    results = db.query_database("""SELECT images.image FROM images INNER JOIN test ON images.Target = test.Target 
                                    WHERE TreatID = %s AND Treatment = %s""", (image_id, treatment,))

    write_file(results, os.path.join(PATH + user_id + "/", name))

    return send_image(user_id, name)


@app.route('/client/<user_id>/<filename>')
def send_image(user_id, filename):
    return send_from_directory(os.path.join(app.static_folder + "/" + user_id), filename)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
    # sess = Session()
    # sess.init_app(app)
