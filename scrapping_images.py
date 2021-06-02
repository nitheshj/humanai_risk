"""
This File scraps all the images and push them to database
"""

import os
import json
import MySQLdb
from collections import OrderedDict
from datetime import datetime
from database import Database
import configparser


def make_string(subdir, file_name):
    """
    This functions takes the path and filename of the json and returns a corresponding string
    :param subdir:
    :param file_name:
    :return:
    """
    with open(subdir + "/" + file_name) as json_file:
        data = json.load(json_file, object_pairs_hook=OrderedDict)
    result = json.dumps(data)

    return result


def insert_variables(connection, cursor, file_path, directory):

    with open(file_path) as json_file:
        data = json.load(json_file, object_pairs_hook=OrderedDict)

    cursor.execute("""SELECT project_id FROM sc_projects WHERE title = %s""", (directory,))
    projectid = int(cursor.fetchone()[0])

    variables = data['variables']
    var_names = [(k["name"],) for k in variables]
    mod_vars = [tuple(each.values()) for each in variables]
    mod_vars = [l + (projectid, projectid) for l in mod_vars]
    mod_vars = [mod_vars[p] + var_names[p] for p in range(len(var_names))]

    cursor.executemany("""INSERT INTO sc_project_variables 
                        (variable_name, initial_value,data_type,research_type, project_id) 
                        SELECT * FROM (SELECT %s, %s, %s, %s, %s) AS tmp
                        WHERE NOT EXISTS (SELECT project_id, variable_name FROM sc_project_variables 
                        WHERE project_id = %s AND variable_name = %s) 
                        LIMIT 1""", mod_vars)
    connection.commit()
    return None


def insert_project(connection, cursor, directory, content, id_post, id_creator):
    """

    :param connection:
    :param cursor:
    :param directory:
    :param content:
    :param id_post:
    :param id_creator:
    :return:
    """
    cursor.execute("""INSERT INTO sc_projects (title, creator_id, json, post_id)
                                        SELECT * FROM (SELECT %s, %s, %s, %s) AS tmp
                                        WHERE NOT EXISTS (SELECT title, creator_id FROM sc_projects WHERE title = %s AND creator_id = %s) 
                                        LIMIT 1""", (directory, id_creator, content, id_post, directory, id_creator))
    connection.commit()
    return None


def insert_scene(connection, cursor, directory, path_dir, one_file):
    """

    :param connection:
    :param cursor:
    :param directory:
    :param path_dir:
    :param one_file:
    :return:
    """
    cursor.execute("""SELECT project_id FROM sc_projects WHERE title = %s""", (directory,))
    project_id = int(cursor.fetchone()[0])
    new_scene = make_string(path_dir, one_file)
    cursor.execute("""INSERT INTO sc_scenes (project_id, title,json) 
                                        SELECT * FROM (SELECT %s, %s, %s) AS tmp
                                        WHERE NOT EXISTS (SELECT title, project_id FROM sc_scenes 
                                        WHERE title = %s AND project_id = %s) 
                                        LIMIT 1""", (project_id, one_file[:-5], new_scene, one_file[:-5], project_id))
    connection.commit()
    return None


def insert_post(connection, cursor, directory, id_creator):
    """
    This function inserts the post and returns the post_id of that insertion.
    :param connection:
    :param cursor:
    :param directory:
    :param id_creator:
    :return:
    """
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_g = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""INSERT INTO wp_posts (post_author, post_title, post_status, post_type, post_date, post_date_gmt, 
                                    post_content, post_content_filtered, post_excerpt, to_ping, pinged) 
                                    SELECT * FROM (SELECT %s, %s, %s, %s, %s, %s, %s as col1, %s as col2, %s as col3, %s as col4, %s as col5) AS tmp 
                                    WHERE NOT EXISTS (SELECT post_title, post_author FROM wp_posts WHERE post_title = %s AND post_author = %s) LIMIT 1""",
                   (id_creator, directory, 'publish', 'project', date, date_g, '', '', '', '', '', directory, id_creator))
    connection.commit()
    cursor.execute("""SELECT ID FROM wp_posts WHERE post_title = %s""", (directory,))
    post = int(cursor.fetchone()[0])

    return post


def insert_image(connection, path_file, identifier):
    """

    :param connection:
    :param cursor:
    :param path_file:
    :param identifier:
    :return:
    """
    thedata = open(path_file, 'rb').read()

    connection.query_database("""UPDATE `chicagofaces`.`images` SET `image` = %s
                     WHERE (`Target` = %s);""", (thedata, identifier,))

    # cursor.execute("""UPDATE `chicagofaces`.`images` SET `image` = %s
    #                  WHERE (`Target` = %s);""", (thedata, identifier))
    connection.cnx.commit()
    return None


def scrapping_main(connection, destination):
    """
    This function inserts both project and scene as strings in the database from JSON files
    :param connection:
    :param cursor:
    :param destination:
    :param creator_id:
    :return:
    """

    root_dir = destination
   
    for each_file in os.listdir(root_dir):
        if each_file[-3:] == 'jpg':
            target = each_file[4:10]
            print (target)
            # insert_project(connection, cursor, dire, new_proj, post_id, creator_id)
            # print (root_dir +'/'+ each_file)
            insert_image(connection, root_dir +'/'+ each_file, target)

        # elif each_file[-4:] == 'json':
        #     insert_scene(connection, cursor, dire, dir_path, each_file)

    return None


if __name__ == '__main__':


    # db_connection = MySQLdb.connect(
    #     host=host,
    #     user=user,
    #     passwd=sword,
    #     port=port,
    #     db=db
    # )
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8-sig')

    db_connection = Database(config)

    # mysql_cursor = db_connection.cursor()

    folder = 'C:/Users/Nithesh/Downloads/Resized'
    # creator_id_number = 97
    scrapping_main(db_connection, folder)
    db_connection.cur.close()
    db_connection.cnx.close()
    # db_connection.close()

    # get_file_name()



