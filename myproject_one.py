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
     allow_headers=["Content-Type", "Origin", "X-Requested-With", "Accept", "x-auth"])
# SESSION_TYPE = 'filesystem'
# SESSION_PERMANENT = False  # Session cookie will expire when browser is closed
app.secret_key = 'human_ai'
app.config.from_object(__name__)
# Session(app)

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')

USERS = dict()


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
    treat = str(request.args.get('treat', "T1"))
    user = str(uuid.uuid4())
    USERS[user] = dict()

    # if treat == "T2":
    #     treatment = 202
    # elif treat == "C":
    #     treatment = 196
    # else:
    #     treatment = 199
    treatment = {'T1': 199, 'T2': 202, 'C': 196}

    # T1 =199, T2 = 202, C = 196
    USERS[user]['sequence'] = random.sample(range(1, treatment[treat]+1), treatment[treat])
    USERS[user]['attention'] = [570, 539, 617, 653, 684, 725, 749, 771, 806, 812]
    return user


@app.route('/out')
def out():
    user = str(request.args.get('user_id'))

    item = USERS.pop(user, "User Don't exist")

    item = "User Popped" if isinstance(item, dict) else item

    return item


@app.route('/api/nextid', methods=['GET'])
def nextid():
    """
    This function randomly chooses an ID from IDs List
    :return
    """
    attention = int(request.args.get('att'))
    user = str(request.args.get('user_id'))

    seq = USERS.get(user, dict()).get('sequence')
    new_choice = random.choice(seq)

    if attention == 0:
        seq.remove(new_choice)
        USERS[user]['sequence'] = seq

    # print(new_choice)

    return str(new_choice)


@app.route('/api/getfico', methods=['GET'])
def getfico():
    """
    This function randomly chooses an ID from IDs List
    :return
    """
    attention = int(request.args.get('att'))
    user = str(request.args.get('user_id'))

    att_seq = USERS.get(user, dict()).get('attention')
    fico = random.choice(att_seq)

    if attention != 0:
        att_seq.remove(fico)
        USERS[user]['attention'] = att_seq

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
    # Convert binary data to proper format and write it on the disk
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'wb+') as file:
        file.write(data)


@app.route('/api/getimage', methods=['GET'])
def getimage():
    image_id = int(request.args.get('image_id'))
    attention = int(request.args.get('att'))
    user_id = str(request.args.get('user_id'))
    treat = str(request.args.get('treat', "T1"))

    if treat == "T2":
        treatment = "T2" if attention == 0 else "T1"
    elif treat == "C":
        treatment = "C" if attention == 0 else "T2"
    else:
        treatment = "T1" if attention == 0 else "C"

    name = 'init.png'

    db = Database(config)

    # T1 =199, T2 = 202, C = 196
    results = db.query_database("""SELECT images.image, test.Credit_rating FROM images INNER JOIN test ON images.Target = test.Target 
                                    WHERE TreatID = %s AND Treatment = %s""", (image_id, treatment,))

    write_file(results[0], os.path.join(PATH + user_id + "/", name))

    return str(results[1])


@app.route('/client/<user_id>/<filename>')
def send_image(user_id, filename):
    return send_from_directory(os.path.join(app.static_folder + "/" + user_id), filename)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
    # sess = Session()
    # sess.init_app(app)
