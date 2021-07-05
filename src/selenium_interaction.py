import logging
import time
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.relative_locator import with_tag_name

from utils import get_args

args = get_args()


class SeleneiumController:

    def __init__(self,
                 webdriver_host,
                 webdriver_port,
                 website_login_user,
                 website_login_password
                 ):
        firefox_options = webdriver.FirefoxOptions()
        self.driver = webdriver.Remote(command_executor=f"{webdriver_host}:{webdriver_port}",
                                       options=firefox_options)

        self.target_website_base = "https://51stregiment.com/"
        self.target_website_login_path = "forum/index.php?action=login"

        self.website_login_user = website_login_user
        self.website_login_password = website_login_password

        self.login()

    def __del__(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    def login(self):
        logging.info(f"Logging in with username {self.website_login_user}")
        self.driver.get(urljoin(self.target_website_base, self.target_website_login_path))
        login_username = self.driver.find_element_by_xpath(
            "/html/body/div[3]/div/div/table/tbody/tr/td/form/div/div[2]/dl[1]/dd[1]/input")
        login_username.send_keys(self.website_login_user)
        login_password = self.driver.find_element_by_xpath(
            "/html/body/div[3]/div/div/table/tbody/tr/td/form/div/div[2]/dl[1]/dd[2]/input")
        login_password.send_keys(self.website_login_password)

        login_btn = self.driver.find_element_by_xpath(
            "/html/body/div[3]/div/div/table/tbody/tr/td/form/div/div[2]/p[1]/input")
        login_btn.click()
        self.driver.save_screenshot("screenshots/login.png")

    def go_to_admin_page(self, event_id):
        """Go to the admin page, given a normal event_id"""
        logging.info(f"Navigating selenium to event id {event_id}")
        event_url = f"https://51stregiment.com/forum/index.php?topic={event_id}.0"
        self.driver.get(event_url)
        event_id_element = self.driver.find_element_by_xpath(
            "/html/body/div[3]/div/div/table/tbody/tr/td/div[1]/div[2]/div/ul/li[2]/form/input[2]")
        admin_event_id = event_id_element.get_attribute("value")
        logging.info(f"Going to admin for event {event_id}. Admin event id is {admin_event_id}")
        self.driver.get(f"https://51stregiment.com/forum/index.php?action=admin_register_event;event={admin_event_id}")
        self.driver.save_screenshot("screenshots/go_to_admin.png")

    def get_name_list(self):
        checkbox_form = self.driver.find_element_by_xpath(
            "/html/body/div[3]/div/div/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td[1]/form")
        name_list = checkbox_form.text.split(sep="\n")[4:]  # First 4 text items are not names
        name_list = [x.strip() for x in name_list]
        return name_list

    def tick_box_for_name(self, name: str):
        logging.info(f"Attempting to tick box for {name}")
        checkbox_form = self.driver.find_element_by_xpath(
            "/html/body/div[3]/div/div/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td[1]/form")

        name_list = self.get_name_list()

        checkbox_list = checkbox_form.find_elements_by_tag_name("input")
        checkbox_list = checkbox_list[3:]

        try:
            my_index = name_list.index(name)  # Finds index of given element in list
        except ValueError:
            logging.warning(f"Not able to find a box for {name}")
            return False
        print(f"Found name at {my_index}")
        checkbox_list[my_index].click()
        logging.info(f"Checked box for {name}")



        self.driver.save_screenshot("screenshots/tick_box_for_name.png")
        return True

    def click_submit(self):
        submit_button = self.driver.find_element(by=By.XPATH,
                                                 value="/html/body/div[3]/div/div/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td[1]/form/p[1]/input")
        logging.debug(f"Clicking submit button - it has text {submit_button.get_attribute(name='value')}")
        # TODO uncomment this if your SURE
        # submit_button.click()