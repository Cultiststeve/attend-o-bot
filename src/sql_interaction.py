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

    def create_event(self,
                     title: str,
                     termsnconns: str = ""):

        add_event_query = "INSERT INTO smf_calendar(title, termsAndCond)\n " \
                    f"VALUES('{title}', '{termsnconns}')"
        self.logger.debug(f"Adding event with: {add_event_query}")
        return myclass.execute_query(query=add_event_query, commit=True)


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

    for table in tables:
        described = myclass.execute_query(f"describe {table[0]};")
        logging.info(f"{table=} : {described=}")

    # myclass.create_event(title="bobs event!")

    res = myclass.execute_query("SELECT * FROM smf_calendar")
    logging.info(f"{res=}")

    logging.info(myclass.execute_query("SELECT * FROM smf_calendar WHERE title='bobs event!'"))

    logging.info(myclass.execute_query("DELETE FROM smf_calendar WHERE title='hellotitle'", commit=True))

    res = myclass.execute_query("SELECT * FROM smf_calendar")
    logging.info(f"{res=}")