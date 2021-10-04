import mysql.connector
import sshtunnel
import pandas as pd
import time


class Database(object):
    def __init__(self, config):
        host = config['database']['hostname']
        user = config['database']['username']
        password = config['database']['password']
        database = config['database']['dbname']

        ssh_host = config['ssh']['host']
        ssh_port = config['ssh']['port']
        ssh_user = config['ssh']['user']
        ssh_pass = config['ssh']['pass']

        with sshtunnel.SSHTunnelForwarder((ssh_host, int(ssh_port)), ssh_username=ssh_user, ssh_password=ssh_pass,
                                          remote_bind_address=(host, 3306)) as tunnel:
            self.cnx = mysql.connector.connect(host=host, user=user, password=password, database=database)
            self.cur = self.cnx.cursor()

    # def store_data(self, user_uuid, game_uuid, agent, game):
    #     """ stores game data into the database """
    #
    #     add_game = ("INSERT INTO studycrafter_wp_db.sc_gamette_games"
    #                 "(game_uuid, num_human_players, study_name, date_time, game_data) "
    #                 "VALUES (%s, %s, %s, %s, %s)")
    #
    #     add_user = ("INSERT INTO studycrafter_wp_db.sc_gamette_users(user_uuid, role, game_id) "
    #                 "VALUES(%(user_uuid)s, %(agent)s, %(game_id)s)")
    #
    #     data_game = (game_uuid, game.num_human_players, game.study_name,
    #                  time.strftime('%Y-%m-%d %H:%M:%S'), game.data.to_json(orient='records'))
    #
    #     self.cur.execute(add_game, data_game)
    #     game_id = self.cur.lastrowid
    #
    #     data_user = {
    #         'user_uuid': str(user_uuid),
    #         'agent': str(agent.agent_name),
    #         'game_id': game_id}
    #
    #     self.cur.execute(add_user, data_user)
    #
    #     self.cnx.commit()
    #
    #     self.cur.close()
    #     self.cnx.close()
    #
    #     return game_id

    def query_database(self, query, values):
        """ query database to select player data and returns results in a data frame"""

        query = (str(query))
        self.cur.execute(query, values)
        results = self.cur.fetchone()

        self.cur.close()
        self.cnx.close()

        return results

    def query_database_all(self, query, values):
        """ query database to select player data and returns results in a data frame"""

        query = (str(query))
        self.cur.execute(query, values)
        results = self.cur.fetchall()

        self.cur.close()
        self.cnx.close()

        return results

    def store_data(self, query, values):
        """ stores game data into the database """

        query = (str(query))
        self.cur.execute(query, values)

        self.cnx.commit()

        self.cur.close()
        self.cnx.close()

        return values

    def store_data_many(self, query, values):
        """ stores game data into the database """

        query = (str(query))
        self.cur.executemany(query, values)

        self.cnx.commit()

        self.cur.close()
        self.cnx.close()

        return values

