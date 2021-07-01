import logging
from typing import Dict

import configargparse


def setup_logging():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("discord").setLevel(logging.INFO)
    logging.getLogger("ts3").setLevel(logging.DEBUG)
    logging.getLogger("selenium").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.INFO)
    logging.getLogger("paramiko").setLevel(logging.INFO)


def get_args() -> Dict:
    parser = configargparse.ArgParser(default_config_files=["default.yml"])
    parser.add_argument('-c', '--my-config', required=True, is_config_file=True, help="Config file path")

    parser.add_argument("--discord_bot_token")
    parser.add_argument("--discord_guild_name")



    parser.add_argument("--ts_url")
    parser.add_argument("--ts_port")
    parser.add_argument("--ts_query_user")
    parser.add_argument("--ts_query_pass")

    parser.add_argument("--webdriver_host")
    parser.add_argument("--webdriver_port")

    parser.add_argument("--51_form_user")
    parser.add_argument("--51_form_pass")

    parser.add_argument("--some_test_var")
    return vars(parser.parse_args())
