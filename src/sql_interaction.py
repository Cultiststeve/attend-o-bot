import datetime
import logging

from mysql.connector import connect, Error

import utils
from utils import get_args

args = get_args()


class SQLInteraction():

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

    def __del__(self):
        try:
            self.connection.close()
        except Exception as e:
            pass

    def select_database(self, db_name: str = "fiftyfirst"):
        self.cursor.execute(f"use {db_name};")
        self.logger.info("Selected fiftyfirst DB")

    def execute_query(self, query: str, commit: bool = False):
        self.logger.debug(f"Executing: {query}")
        self.cursor.execute(query)
        if commit: self.connection.commit()
        return self.cursor.fetchall()

    def add_member(self):
        """Only use localy for test purposes"""
        if self.connection.server_host != "localhost":
            raise Exception("Do not add new members outside of local DB, dummy")
        query = "INSERT INTO smf_members(member_name, buddy_list, message_labels, openid_uri, signature, ignore_boards) " \
                "VALUES('cultiststeve', '', '', '', '', '')"
        self.logger.debug(f"Adding member with: {query}")
        return myclass.execute_query(query=query, commit=True)

    def create_event(self,
                     title: str,
                     start_date=datetime.date.today(),
                     end_date=datetime.date.today(),
                     max_attendants=1000,
                     termsnconns: str = ""):

        add_event_query = "INSERT INTO smf_calendar(title, start_date, end_date, maxAttendants, termsAndCond) " \
                          f"VALUES('{title}', '{start_date}', '{end_date}', '{max_attendants}', '{termsnconns}')"
        self.logger.debug(f"Adding event with: {add_event_query}")
        return myclass.execute_query(query=add_event_query, commit=True)

    def add_attendee_to_event(self,
                              id_event,
                              id_member,
                              # dateRegistered=0,
                              # dateConfirmed=0,
                              # dateRegistered=datetime.date.today(),
                              # dateConfirmed=datetime.date.today(),
                              registrant="attend-o-bot",
                              comment=""):
        # add_attendee_query = "INSERT INTO smf_calendar_reg(dateRegistered, ID_EVENT, ID_MEMBER, dateConfirmed, registrant, comment) " \
        #                      f"VALUES('{dateRegistered}', '{id_event}', '{id_member}', '{dateConfirmed}', '{registrant}', '{comment}')"

        add_attendee_query = "INSERT INTO smf_calendar_reg(ID_EVENT, ID_MEMBER, registrant, comment) " \
                             f"VALUES('{id_event}', '{id_member}', '{registrant}', '{comment}')"
        self.logger.debug(f"Adding attendee with: {add_attendee_query}")
        return myclass.execute_query(query=add_attendee_query, commit=True)


if __name__ == "__main__":
    utils.setup_logging()

    myclass = SQLInteraction(
        host=args["sql_host"],
        user=args["sql_user"],
        password=args["sql_pass"]
    )
    myclass.select_database()

    tables = myclass.execute_query("show tables")
    logging.info(f"{tables=}")

    # for table in tables:
    #     described = myclass.execute_query(f"describe {table[0]};")
    #     logging.info(f"{table=} : {described=}")

    # myclass.create_event(title="bobs event 2!")

    # res = myclass.execute_query("SELECT * FROM smf_calendar")
    # logging.info(f"{res=}")

    # logging.info(myclass.execute_query("SELECT * FROM smf_calendar WHERE title='bobs event!'"))

    # logging.info(myclass.execute_query("DELETE FROM smf_calendar WHERE title='hellotitle'", commit=True))

    select_bob = myclass.execute_query("SELECT * FROM smf_calendar WHERE title='bobs event 2!'")
    print(f"{select_bob=}")
    # bobs event 2, id = 925

    # myclass.add_member()
    # print(myclass.execute_query("SELECT * FROM smf_members WHERE member_name='cultiststeve'"))
    # cultiststeve = 2764


    add_attendee = myclass.add_attendee_to_event(id_event=925, id_member=2764)
    print(f"{add_attendee=}")

    all_attendance = myclass.execute_query("SELECT * FROM smf_calendar_reg")
    print(f"{all_attendance=}")

