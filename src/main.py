import logging

import src.discord_bot_control
from src.discord_bot_control import bot as discord_bot
from src.teamspeak_querying import TeamspeakQueryControl
from src.selenium_interaction import SeleneiumController
import src.utils as utils


def main():
    utils.setup_logging()
    main_logger = logging.getLogger("main")

    main_logger.info("Start of program")

    args = utils.get_args()
    main_logger.debug(f"Prog args: {args}")

    src.discord_bot_control.teamspeak_query_controller = TeamspeakQueryControl(query_username=args.get("ts_query_user"),
                                                                               query_password=args.get("ts_query_pass"),
                                                                               server_url=args.get("ts_url"),
                                                                               server_port=args.get("ts_port"))

    # TODO try except
    src.discord_bot_control.selenium_controller = SeleneiumController(webdriver_host=args.get("webdriver_host"),
                                                                      webdriver_port=args.get("webdriver_port"),
                                                                      website_login_user=args.get("51_form_user"),
                                                                      website_login_password=args.get("51_form_pass")
                                                                      )

    discord_bot.run(args.get("discord_bot_token"))


if __name__ == "__main__":
    main()
