import logging

import src.discord_bot_control

from src.discord_bot_control import bot as discord_bot

from src.teamspeak_querying import TeamspeakQueryControl
from src.sql_interaction import SQLInteraction
import src.utils as utils


def main():
    utils.setup_logging()
    main_logger = logging.getLogger("main")

    main_logger.info("Start of program")

    args = utils.get_args()
    main_logger.debug(f"Prog args: {args}")

    main_logger.info("Creating TS3 Query Control")
    src.discord_bot_control.teamspeak_query_controller = TeamspeakQueryControl(query_username=args.get("ts_query_user"),
                                                                               query_password=args.get("ts_query_pass"),
                                                                               server_url=args.get("ts_url"),
                                                                               server_port=args.get("ts_port"))

    main_logger.info("Creating SQL interaction controller for the bot")
    src.discord_bot_control.sql_controller = SQLInteraction(
        host=args["sql_host"],
        user=args["sql_user"],
        password=args["sql_pass"]
    )

    discord_bot.add_cog(src.discord_bot_control.AttendanceFunctions(discord_bot))

    discord_bot.run(args.get("discord_bot_token"))


if __name__ == "__main__":
    main()
