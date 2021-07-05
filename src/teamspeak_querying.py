import logging
from typing import Dict, List

import ts3


class TeamspeakQueryControl:

    def __init__(self, query_username, query_password, server_url, server_port, SID=1):
        self.ts3conn = ts3.query.TS3ServerConnection(
            f"ssh://{query_username}:{query_password}@{server_url}:{server_port}")
        self.ts3conn.exec_("use", sid=SID)

    def list_all_clients(self) -> List:
        logging.info("Listing all clients")
        resp = self.ts3conn.query(cmd="clientlist").fetch()
        return resp.parsed

    def list_all_channels(self) -> List:
        logging.info("Listing all channels")
        resp = self.ts3conn.query(cmd="channellist").fetch()
        return resp.parsed

    def get_client_info(self, clid):
        resp = self.ts3conn.query(f"clientinfo", clid=clid).fetch()
        return resp.parsed

