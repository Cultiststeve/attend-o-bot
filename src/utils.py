import logging
from typing import Dict

import configargparse


def setup_logging():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("discord").setLevel(logging.INFO)
    logging.getLogger("ts3").setLevel(logging.DEBUG)


def get_args() -> Dict:
    parser = configargparse.ArgParser(default_config_files=["default.yml"])
    parser.add_argument('-c', '--my-config', required=True, is_config_file=True, help="Config file path")
    parser.add_argument("--discord_bot_token", help="Discord bot token")
    parser.add_argument("--51_form_user_name")
    parser.add_argument("--51_form_password")

    parser.add_argument("--some_test_var")
    return vars(parser.parse_args())
