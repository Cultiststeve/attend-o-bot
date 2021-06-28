import time

import ts3


sever_url = "127.0.0.1"


query_acc_user = "generic_user_1"
query_acc_password = "eVRrzG07"

SID = 1


def list_all_clients(ts3conn):
    resp = ts3conn.query(cmd="clientlist").fetch()

    client_list = resp.data[0]
    client_list = client_list.decode("utf-8")
    client_list = client_list.split('|')
    return client_list


def get_cid_of_channel_name(name: str):
    channel_list = ts3conn.query("channellist").all()
    for channel in channel_list:
        if channel["channel_name"] == name:
            return channel["cid"]
    return None


def get_clients_in_cid(search_cid: int):
    client_list = ts3conn.query("clientlist").all()
    in_channel_clients = []
    for client in client_list:
        if client["cid"] == search_cid:
            in_channel_clients.append(client)

    return in_channel_clients


with ts3.query.TS3ServerConnection(f"ssh://{query_acc_user}:{query_acc_password}@localhost:10022") as ts3conn:
    ts3conn.exec_("use", sid=SID)

    cid_important = get_cid_of_channel_name("channelfour")

    res = get_clients_in_cid(cid_important)

    print(res)

