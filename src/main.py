import logging

from src.discord_bot_control import bot as discord_bot
from src.teamspeak_querying import TeamspeakInfoGetter
import src.utils as utils

query_acc_user = "generic_user_1"
query_acc_password = "eVRrzG07"
TOKEN = """ODU4ODE5MjA4ODg3NjY0NjYw.YNjrtw.5hFs718L9xbpvYmk0SGDfQP-SYA"""
GUILD = "Cultiststeve's playground"
GUILD_ID = 706588450731851847


def main():
    utils.setup_logging()
    main_logger = logging.getLogger("main")

    main_logger.info("Start of program")

    args = utils.get_args()
    main_logger.debug(f"Prog args: {args}")

    exit()

    teamspeak_getter = TeamspeakInfoGetter(query_username=query_acc_user,
                                           query_password=query_acc_password)

    clients = teamspeak_getter.list_all_clients()
    print(clients)

    discord_bot.run(TOKEN)


if __name__ == "__main__":
    main()
