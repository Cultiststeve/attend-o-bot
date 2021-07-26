from src.teamspeak_querying import TeamspeakQueryControl
from src.selenium_interaction import SeleneiumController
from src.utils import get_args

args = get_args()

teamspeak_query_controller = TeamspeakQueryControl(query_username=args.get("ts_query_user"),
                                                   query_password=args.get("ts_query_pass"),
                                                   server_url=args.get("ts_url"),
                                                   server_port=args.get("ts_port"))

selenium_controller = SeleneiumController(webdriver_host=args.get("webdriver_host"),
                                          webdriver_port=args.get("webdriver_port"),
                                          website_login_user=args.get("51_form_user"),
                                          website_login_password=args.get("51_form_pass")
                                          )

# res = teamspeak_query_controller.list_all_clients()

selenium_controller.login()
selenium_controller.go_to_admin_page(admin_event_id=3045)

# print(website_names)
pass
