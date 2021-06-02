"""
This script contains the functions necessary for the complex operations that can't be performed in Game Scriptor
@author: Nithesh Javvaji
@date: 08-18-2020
@project: Tier-1 Human AI Collaboration

"""
from datetime import datetime
import uuid
# import jwt
import pandas as pd
# import numpy as np
from flask import Flask, request, send_from_directory
from sklearn.metrics import mean_squared_error
# from flask import session
# from flask_session import Session
from database import Database
import configparser
# import math
import random
import os
from flask_cors import CORS
from ml_model import ModelRun
# import pickle

PATH = os.path.join(os.path.abspath('..'), 'Tier1/client/')

app = Flask(__name__, static_url_path="", static_folder=PATH)
app.secret_key = 'human_ai'
app.config.from_object(__name__)
CORS(app, resources={r"/*": {"origins": "https://studycrafter.com"}}, supports_credentials=True,
     allow_headers=["Content-Type", "Origin", "X-Requested-With", "Accept", "x-auth"])

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')

USERS = dict()


@app.route('/set')
def start():
    """

    :return:
    """
    #ToDo-Done
    treat = str(request.args.get('treat', "T1"))
    # treat = 'T1'
    user = str(uuid.uuid4())
    USERS[user] = dict()

    treatment = {'T1': 199, 'T2': 202, 'C': 196}

    # T1 =199, T2 = 202, C = 196
    USERS[user]['one'] = random.sample(range(1, treatment[treat]+1), treatment[treat])
    USERS[user]['att1'] = [570, 539, 617, 653, 684, 725, 749, 771, 806, 812]
    USERS[user]['att2'] = [575, 534, 602, 663, 691, 729, 769, 777, 811, 823]
    USERS[user]['user_choice'] = [0] * treatment[treat]
    USERS[user]['two'] = random.sample(range(1, treatment['C']+1), 50)
    USERS[user]['user_choice_2'] = dict()
    USERS[user]['reco_actual'] = dict()

    return user

def compute_rmse(first_dict:dict,second_dict:dict):
    first_list = list()
    second_list = list()

    for each in first_dict.keys():
        first_list.append(first_dict[each])
        second_list.append(second_dict[each])

    rmse = mean_squared_error(first_list,second_list,squared=False)

    return rmse

@app.route('/out')
def out():
    user = str(request.args.get('user_id'))

    test_ideal_rmse = float(compute_rmse(USERS[user]['user_choice_2'],USERS[user]['recommendations']))
    test_actual_rmse = float(compute_rmse(USERS[user]['user_choice_2'],USERS[user]['reco_actual']))
    train_rmse = float(USERS[user]['train_rmse'])

    db = Database(config)

    db.store_data("""INSERT INTO chicagofaces.player_model(user, train_rmse,test_actual_rmse,test_ideal_rmse)
                            VALUES (%s,%s,%s,%s);""",
                  (user, train_rmse, test_actual_rmse, test_ideal_rmse,))

    item = USERS.pop(user, "User Don't exist")

    item = "User Popped" if isinstance(item, dict) else item

    return item


@app.route('/api/storechoice', methods=['GET'])
def storechoice():
    """
    This function randomly chooses an ID from IDs List
    :return
    """
    image_id = int(request.args.get('image_id'))
    phase = str(request.args.get('phase'))
    user = str(request.args.get('user_id'))
    user_choice = int(request.args.get("choice"))
    treat = str(request.args.get("treat"))
    react_time = int(request.args.get("time"))
    recommendation = str(request.args.get("rec"))
    timenow = datetime.now()

    if phase == 'one':
        USERS[user]['user_choice'][image_id-1] = user_choice
    elif phase == 'two':
        USERS[user]['user_choice_2'][image_id] = user_choice

    #ToDo- save choices to database-done
    db = Database(config)

    db.store_data("""INSERT INTO chicagofaces.player_decisions(datetime, user, treatment, phase, image_id, choice, reactiontime,reco)
                        VALUES (%s,%s, %s,%s,%s,%s,%s,%s);""",
                        (timenow, user, treat, phase, image_id, user_choice, react_time, recommendation,))

    return phase


@app.route('/api/nextid', methods=['GET'])
def nextid():
    """
    This function randomly chooses an ID from IDs List
    :return
    """
    phase = str(request.args.get('phase'))
    user = str(request.args.get('user_id'))

    phase_var = "two" if phase == "att1" or phase == "att2" else phase
    seq = USERS.get(user, dict()).get(phase_var)
    new_id = random.choice(seq)

    if phase == 'one' or phase == 'two':
        seq.remove(new_id)
        USERS[user][phase] = seq

    return str(new_id)


@app.route('/api/getfico', methods=['GET'])
def getfico():
    """
    Send fico scores for attention check faces
    :return fico score as string
    """
    phase = str(request.args.get('phase'))
    user = str(request.args.get('user_id'))

    att_seq = USERS.get(user, dict()).get(phase)
    fico = random.choice(att_seq)

    if phase == "att1" or phase == "att2":
        att_seq.remove(fico)
        USERS[user][phase] = att_seq

    # print(fico)

    return str(fico)


@app.route('/api/getcredit', methods=['GET'])
def getcredit():
    """
    (NOT IN USE ANYMORE)
    Retrieve credit rating of an image
    :return:
    """
    db = Database(config)
    image_id = int(request.args.get('image_id'))

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
    phase = str(request.args.get('phase'))
    user_id = str(request.args.get('user_id'))
    treat = str(request.args.get('treat', "T1"))

    treatment = str()
    if treat == "T1":
        treatment = "C" if phase == "att1" else treat
    elif treat == "T2":
        treatment = "C" if phase == "att1" else treat
    elif treat == "C":
        treatment = "T2" if phase == "att2" else treat

    db = Database(config)

    # T1 =199, T2 = 202, C = 196
    results = db.query_database("""SELECT images.image, test.Credit_rating FROM images INNER JOIN test ON images.Target = test.Target 
                                    WHERE TreatID = %s AND Treatment = %s""", (image_id, treatment,))

    name_image = 'init.png'
    write_file(results[0], os.path.join(PATH + user_id + "/", name_image))

    return str(results[1])


@app.route('/client/<user_id>/<filename>')
def send_image(user_id, filename):
    return send_from_directory(os.path.join(app.static_folder + "/" + user_id), filename)


@app.route('/api/runmodel', methods=['GET'])
def runmodel():
    #ToDo-Done
    user = str(request.args.get('user_id'))
    treat = str(request.args.get('treat', "T1"))

    data = pd.read_csv('game_face_data_'+treat+'.csv')
    data['User_choice'] = USERS[user]['user_choice']

    # testing
    # test = {"Poor": '1', "Fair": '1', "Good": '3', "Very Good": '5', "Exceptional": '5'}
    # data['User_choice'] = data['Credit_rating'].map(test)
    # treatment = {'T1': 199, 'T2': 202, 'C': 196}
    # data['User_choice'] = np.random.uniform(low=1, high=5, size=(treatment[treat],))

    mod = ModelRun(dataset_csv=data)
    mod.whole_procedure(user)
    USERS[user]['train_rmse'] = mod.rf_rmse

    pred = ModelRun(pd.read_csv('game_face_data_C.csv'))
    USERS[user]['recommendations'] = pred.rec(user)

    return treat


@app.route('/api/getreco', methods=['GET'])
def getreco():
    """

    :return:
    """
    image_id = int(request.args.get('image_id'))
    user_id = str(request.args.get('user_id'))

    result = USERS[user_id]['recommendations'][image_id]

    if 0 <= result <= 1.5:
        result = 1
    elif 1.5 < result <= 2.5:
        result = 2
    elif 2.5 < result <= 3.5:
        result = 3
    elif 3.5 < result <= 4.5:
        result = 4
    elif 4.5 < result <= 5.5:
        result = 5

    USERS[user_id]['reco_actual'][image_id] = result

    return str(result)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # ToDo - done
    app.run(host='0.0.0.0', debug=True, threaded=True)

