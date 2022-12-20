import configparser
import csv
import json
import sys
import re
from collections import OrderedDict
from database import Database
import pandas as pd

def compute_attention(sequence):
    """

    :param sequence:
    :return:
    """

    keyname = str()
    att_choices = dict()

    for item in sequence["scenes"]:
        if item["scene_name"] == "LoanDecisions":
            for each in item["variables_set"]:
                if each["name"] == "fico":
                    keyname = each["value"]

                if each["name"] == "Choice_att":
                    att_choices[keyname] = each["value"]

    att_values = {"570": "1", "539": "1", "617": "2", "653": "2", "684": "3", "725": "3", "749": "4", "771": "4", "806": "5", "812": "5"}

    score = 0
    for each in att_choices.keys():
        try:
            if att_choices[each] == att_values[each]:
                score += 1 if score < 4 else 0
        except KeyError:
            print("test")
            score += 1 if score < 4 else 0

    return score


def extract_fieldnames(json_string):
    """

    :param json_string:
    :return:
    """

    sequence = json.loads(json_string, object_pairs_hook=OrderedDict)
    variables = list(element["name"] for element in sequence["variable_values"])

    variables.remove("user_id")
    variables.insert(0, "user_id")

    return variables


def extract_user_vars(sequen):
    """

    :param sequen:
    :return:
    """

    var_seq = dict()

    for element in sequen["variable_values"]:
        keyname = element["name"]
        var_seq[keyname] = element["value"]

    return var_seq


def sequence_parser(sequen):
    """

    :param sequen:
    :return:
    """

    choice_seq = dict()
    keyname = "user"

    for element in sequen["variable_values"]:
        if element["name"] == "user_id":
            choice_seq[keyname] = element["value"]
            break

    for item in sequen["scenes"]:
        if item["scene_name"] == "LoanDecisions":
            for each in item["variables_set"]:
                if each["name"] == "id":
                    keyname = 'Face_' + str(each["value"])

                if each["name"] == "Choice":
                    choice_seq[keyname] = each["value"]

    return choice_seq


def clean_up_string(text_object):
    """
    This fucntions cleans the INTERNAL SERVER 500 errors received from the server
    :param text_object: json string obtained from the database
    :return:
    """
    locations =  [m.start() for m in re.finditer("<!", text_object)]

    for i, each in enumerate(locations):
        text_object = text_object[:each-(i*294)] + text_object[each-(i*294)+294:]

    return text_object


def extracting_main(connection, destination, file_name, project_id):
    """

    :return:
    """
    groups = {'T1': 199, 'T2': 202, 'C': 196}
    ids = {'T1': 1435, 'T2': 1438, 'C': 1439}

    # result = connection.query_database_all("""select json,end_time from studycrafter_wp_db.sc_analytics
    #                                             where project_id = %s""", (ids[group],))

    result = connection.query_database_all("""select json,end_time from studycrafter_wp_db.sc_analytics 
                                            where project_id = %s""", (project_id, ))

    data_out = file_name  # sys.argv[2]
    count = 0

    with open(data_out, 'w', newline='', encoding="utf-8") as destname:

        # var_fields = list("Face_" + str(number) for number in range(1, groups[group]+1))
        new_string = clean_up_string(result[-1][0])
        var_fields = extract_fieldnames(new_string)
        var_fields.insert(1, "time")
        # var_fields.insert(0,"user")
        var_fields.insert(2, "attention_score")
        var_fields.insert(0, "row_id")
        writer = csv.DictWriter(destname, fieldnames=var_fields, restval='NA', extrasaction='ignore')
        writer.writeheader()

        for row in result:
            try:
                count += 1
                row_text = clean_up_string(row[0])
                sequence = json.loads(row_text, object_pairs_hook=OrderedDict)
                # formatted_row = sequence_parser(sequence)
                formatted_row = extract_user_vars(sequence)
                formatted_row["time"] = float(row[1])
                formatted_row["row_id"] = count
                formatted_row["attention_score"] = compute_attention(sequence)
                writer.writerow(formatted_row)
            except json.decoder.JSONDecodeError:
                # z = len(row[0])
                # adj_row = row[0].replace(repr("""<!DOCTYPE HTML PUBLIC "- //W3C//DTD HTML 3.2 Final//EN">\n<title>500 Internal Server Error</title>\n<h1>Internal Server Error</h1>\n<p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>\n"""),"")
                try:
                    print("failed first attempt")
                    x = row[0].find("<")
                    # w = len("""<!DOCTYPE HTML PUBLIC "- //W3C//DTD HTML 3.2 Final//EN">\n<title>500 Internal Server Error</title>\n<h1>Internal Server Error</h1>\n<p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>\n""")
                    adj_row = row[0][:x] + row[0][x+291:]
                    # y = len(adj_row)
                    sequence = json.loads(adj_row, object_pairs_hook=OrderedDict)
                    # formatted_row = sequence_parser(sequence)
                    formatted_row = extract_user_vars(sequence)
                    formatted_row["time"] = float(row[1])
                    formatted_row["row_id"] = count
                    formatted_row["attention_score"] = compute_attention(sequence)
                    writer.writerow(formatted_row)
                except json.decoder.JSONDecodeError:
                    print("skipped row:", count)

        print ("Extraction of user demographics from database JSON files completed!")


def combine_data(decision_data_file, demographics_data_file, final_output_file):
    """
    Combines the csv files with participant decisions (external) and  participant demographics (from previous step)
    :param decision_data_file:
    :param demographics_data_file:
    :param final_output_file:
    :return:
    """

    face_data = pd.read_csv(decision_data_file)

    user_data = pd.read_csv(demographics_data_file)

    user_data = user_data[['user_id','time','study_id','Q15','Q16','Q17','Q18','Q19','Q_open_exp']]
    user_data.rename(columns={'user_id':'user','Q15': 'P_Age', 'Q16': 'P_Gender','Q17': 'P_Intl_student','Q18': 'P_Race','Q19': 'P_Income'}, inplace=True)

    new = pd.merge(face_data, user_data, how='left', on=['user'])

    new.to_csv(final_output_file, encoding='utf-8')

    print("combined data files!")


if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read('config_SC.ini', encoding='utf-8-sig')

    db_connection = Database(config)

    folder = 'C:/Users/Nithesh/Google Drive/Tier1/DataAnalysis/'
    demo_file = folder + 'Study_2_Main_userdata.csv'
    dec_file = folder + 'Study_2_Main_raw_data.csv'
    output = folder + 'Study_2_Main_fulldata.csv'
    sc_project_id = 1882 #1882-S2V5, 1960- admissionss1v1

    extracting_main(db_connection, folder, demo_file, sc_project_id)

    combine_data(dec_file,demo_file,output)
