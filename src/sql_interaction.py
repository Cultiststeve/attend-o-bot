import datetime
import logging

from mysql.connector import connect, Error

import utils
from utils import get_args

args = get_args()


class SQLInteraction:

    def __init__(self,
                 host,
                 user,
                 password,
                 ):
        self.logger = logging.getLogger("root.SQLInteraction")
        self.connection = connect(
            host=host, user=user, password=password
        )
        self.cursor = self.connection.cursor()
        self.id_member = 2764  # TODO what is the ID of our bot poster
        self.bot_name = "attend-o-tron"
        self.bot_email = "attendance@fidyfirst.com"
        self.bot_ip = "192.168.0.256"
        self.select_database()

    def __del__(self):
        try:
            self.connection.close()
        except Exception as e:
            pass

    def select_database(self, db_name: str = "fiftyfirst"):
        # TODO DB name?
        self.cursor.execute(f"use {db_name};")
        self.logger.info("Selected fiftyfirst DB")

    def execute_query(self, query: str, commit: bool = False):
        self.logger.debug(f"Executing: {query}")
        self.cursor.execute(query)
        if commit: self.connection.commit()
        return self.cursor.fetchall()

    def add_member(self, member_name):
        """Only use locally for test purposes"""
        if self.connection.server_host != "localhost":
            raise Exception("Do not add new members outside of local DB, dummy")
        query = "INSERT INTO smf_members(member_name, buddy_list, message_labels, openid_uri, signature, ignore_boards) " \
                f"VALUES('{member_name}', '', '', '', '', '')"
        self.logger.debug(f"Adding member with: {query}")
        return self.execute_query(query=query, commit=True)

    def create_event(self,
                     title: str,
                     start_date=datetime.date.today(),
                     end_date=datetime.date.today(),
                     max_attendants=1000,
                     termsnconns: str = "",
                     id_board=12):
        """Add event (and corresponding thread + message)"""
        self.logger.info(f"Adding event with {title}")

        # TODO id_board? - maybe 12

        add_topic = "INSERT INTO smf_topics(id_board, id_member_started, id_member_updated, num_replies) " \
                    f"VALUES('{id_board}', '{self.id_member}', '{self.id_member}', '1')"
        self.execute_query(query=add_topic)
        id_topic = self.cursor.lastrowid
        # TODO previous board and topic?

        add_msg = "INSERT INTO smf_messages(id_topic, id_board, poster_time, id_member, subject, " \
                  "poster_name, poster_email, poster_ip, body) " \
                  f"VALUES('{id_topic}', '{id_board}', UNIX_TIMESTAMP(), '{self.id_member}', '{title}', " \
                  f"'{self.bot_name}', '{self.bot_email}', '{self.bot_ip}', '{title}')"
        self.execute_query(query=add_msg)
        id_message = self.cursor.lastrowid
        # TODO poster time, id_msg_modified, poster_email, poster_ip, icon

        # Update the topic with the message we just added
        self.execute_query(f"UPDATE smf_topics "
                           f"SET id_first_msg='{id_message}', id_last_msg='{id_message}'  "
                           f"WHERE id_topic={id_topic}")

        add_event_query = "INSERT INTO smf_calendar(title, start_date, end_date, id_board, id_topic, maxAttendants, termsAndCond, id_member) " \
                          f"VALUES('{title}', '{start_date}', '{end_date}', '{id_board}', '{id_topic}', '{max_attendants}', '{termsnconns}', '{self.id_member}')"
        self.execute_query(query=add_event_query, commit=True)
        id_event = self.cursor.lastrowid

        return id_event

    def add_attendee_to_event(self,
                              id_event,
                              id_member,
                              registrant=None,
                              comment=""):
        if not registrant: registrant = self.bot_name  # cant do a self ref default in func def
        add_attendee_query = "INSERT INTO smf_calendar_reg(dateRegistered, ID_EVENT, ID_MEMBER, dateConfirmed, registrant, comment) " \
                             f"VALUES(UNIX_TIMESTAMP(), '{id_event}', '{id_member}', UNIX_TIMESTAMP(), '{registrant}', '{comment}')"

        self.logger.debug(f"Adding attendee with: {add_attendee_query}")
        return self.execute_query(query=add_attendee_query, commit=True)

    def get_all_users(self):
        """Returns a list of tuples, with user rows"""
        see_users = "SELECT * FROM smf_members"
        return self.execute_query(see_users)

    def print_all_tables(self):
        print("top: " + str(self.execute_query("SELECT * FROM smf_topics")))
        print("msg: " + str(self.execute_query("SELECT * FROM smf_messages")))
        print("cal: " + str(self.execute_query("SELECT * FROM smf_calendar")))
        print("crg: " + str(self.execute_query("SELECT * FROM smf_calendar_reg")))
        print("mem: " + str(self.execute_query("SELECT * FROM smf_members")))


if __name__ == "__main__":
    utils.setup_logging()

    myclass = SQLInteraction(
        host=args["sql_host"],
        user=args["sql_user"],
        password=args["sql_pass"]
    )


    # tables = myclass.execute_query("show tables")
    # logging.info(f"{tables=}")

    # for table in tables:
    #     described = myclass.execute_query(f"describe {table[0]};")
    #     logging.info(f"{table=} : {described=}")

    # myclass.add_member()
    # print(myclass.execute_query("SELECT * FROM smf_members WHERE member_name='cultiststeve'"))
    # cultiststeve = 2764

    # add_attendee = myclass.add_attendee_to_event(id_event=927, id_member=2764)

    def delete_all():
        myclass.execute_query("DELETE FROM smf_topics WHERE id_board=12")
        myclass.execute_query("DELETE FROM smf_messages WHERE id_board=12")
        myclass.execute_query("DELETE FROM smf_calendar WHERE id_board=12")
        myclass.execute_query("DELETE FROM smf_calendar_reg WHERE registrant='attend-o-tron'", commit=True)


    delete_all()
    myclass.create_event(title="Sunday Naval")

    myclass.print_all_tables()

    # myclass.add_member("sparky")

    # users = myclass.get_all_users()
    # print(f"Currently {len(users)} users in the db")
