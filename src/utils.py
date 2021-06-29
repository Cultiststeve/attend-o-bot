import logging

import configargparse


def setup_logging():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("discord").setLevel(logging.INFO)


def get_args():
    parser = configargparse.ArgParser()
    return parser.parse_args()