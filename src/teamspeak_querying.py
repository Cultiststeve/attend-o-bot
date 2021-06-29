import ts3



class TeamspeakInfoGetter:

    def __init__(self, query_username, query_password, server_url="localhost", SID=1):
        self.ts3conn = ts3.query.TS3ServerConnection(f"ssh://{query_username}:{query_password}@{server_url}:10022")
        self.ts3conn.exec_("use", sid=SID)

    def list_all_clients(self):
        resp = self.ts3conn.query(cmd="clientlist").fetch()

        client_list = resp.data[0]
        client_list = client_list.decode("utf-8")
        client_list = client_list.split('|')
        return client_list

    def get_cid_of_channel_name(self, name: str):
        channel_list = self.ts3conn.query("channellist").all()
        for channel in channel_list:
            if channel["channel_name"] == name:
                return channel["cid"]
        return None

    def get_clients_in_cid(self, search_cid: int):
        client_list = self.ts3conn.query("clientlist").all()
        in_channel_clients = []
        for client in client_list:
            if client["cid"] == search_cid:
                in_channel_clients.append(client)

        return in_channel_clients
