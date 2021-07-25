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

    def get_children_channels(self, pid: str):
        """Given a cid, get all children

        Args:
            pid: the cid of the parent channel (pid)
        """
        all_channels = self.list_all_channels()
        for x in all_channels:
            print(x.get("pid"))
        res = [x for x in all_channels if x.get("pid") == pid]
        return res

    def get_children_named_channels(self, target_channel_names: List[str]):
        """Given a list of channel names, return a list of all of their children"""
        target_channel_names = [x.strip() for x in target_channel_names]
        all_channels = self.list_all_channels()
        target_channel_cids = []
        for target_channel in target_channel_names:
            for channel in all_channels:
                if channel.get("channel_name") == target_channel:
                    target_channel_cids.append(channel.get("cid"))  # get cid of the named channel

        target_children = []
        for target_channel_cid in target_channel_cids:
            target_children.append(self.get_children_channels(target_channel_cid))
        return target_children

    def get_client_info(self, clid):
        resp = self.ts3conn.query(f"clientinfo", clid=clid).fetch()
        return resp.parsed

    def keep_conn_alive(self):
        self.ts3conn.send_keepalive()


if __name__ == "__main__":
    import src.utils as utils

    args = utils.get_args()
    teamspeak_query_controller = TeamspeakQueryControl(query_username=args.get("ts_query_user"),
                                                                               query_password=args.get("ts_query_pass"),
                                                                               server_url=args.get("ts_url"),
                                                                               server_port=args.get("ts_port"))

    # channels = teamspeak_query_controller.list_all_channels()
    # print(channels)

    children = teamspeak_query_controller.get_children_named_channels(target_channel_names=["Server 1", "Server 2"])
    print(children)
    pass