import logging

import configargparse


def setup_logging():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("discord").setLevel(logging.INFO)
    logging.getLogger("ts3").setLevel(logging.DEBUG)


def get_args():
    parser = configargparse.ArgParser(default_config_files=["default.yml"])
    parser.add_argument('-c', '--my-config', required=True, is_config_file=True, help="Config file path")
    parser.add_argument("--discord_bot_token", help="Discord bot token")

    parser.add_argument("--some_test_var")
    return parser.parse_args()
