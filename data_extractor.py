import configparser
import csv
import json
import sys
from collections import OrderedDict
from database import Database


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

    att_values = {"570": "5", "539": "5", "617": "4", "653": "4", "684": "3", "725": "3", "749": "2", "771": "2", "806": "1", "812": "1"}

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


def extracting_main(connection, destination, group):
    """

    :return:
    """
    groups = {'T1': 199, 'T2': 202, 'C': 196}
    ids = {'T1': 1435, 'T2': 1438, 'C': 1439}

    # result = connection.query_database_all("""select json,end_time from studycrafter_wp_db.sc_analytics
    #                                             where project_id = %s""", (ids[group],))

    result = connection.query_database_all("""select json,end_time from studycrafter_wp_db.sc_analytics 
                                            where project_id = %s or project_id = %s or project_id = %s""", (1435, 1438, 1439, ))

    # data_out = 'gamedata_test_'+ group +'.csv'  # sys.argv[2]
    data_out = 'user_test_all' + '.csv'  # sys.argv[2]
    count = 0

    with open(data_out, 'w', newline='', encoding="utf-8") as destname:

        # var_fields = list("Face_" + str(number) for number in range(1, groups[group]+1))
        var_fields = extract_fieldnames(result[-1][0])
        var_fields.insert(1, "time")
        # var_fields.insert(0,"user")
        var_fields.insert(2, "attention_score")
        var_fields.insert(0, "row_id")
        writer = csv.DictWriter(destname, fieldnames=var_fields, restval='NA', extrasaction='ignore')
        writer.writeheader()

        for row in result:
            try:
                count += 1
                sequence = json.loads(row[0], object_pairs_hook=OrderedDict)
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


if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read('config_SC.ini', encoding='utf-8-sig')

    db_connection = Database(config)

    folder = 'DataAnalyis/'
    treatment = str(sys.argv[1])
    extracting_main(db_connection, folder, treatment)
