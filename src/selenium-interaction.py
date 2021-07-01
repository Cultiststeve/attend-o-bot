import time
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.relative_locator import with_tag_name

from utils import get_args
args = get_args()

webdriver_host = "http://localhost"
webdriver_port = "4444"

target_website_base = "https://51stregiment.com/"

target_website_login_path = "forum/index.php?action=login"

firefox_options = webdriver.FirefoxOptions()
driver = webdriver.Remote(command_executor=f"{webdriver_host}:{webdriver_port}",
                          options=firefox_options)


def login():
    driver.get(urljoin(target_website_base, target_website_login_path))
    login_username = driver.find_element_by_xpath("/html/body/div[3]/div/div/table/tbody/tr/td/form/div/div[2]/dl[1]/dd[1]/input")
    login_username.send_keys(args["51_form_user_name"])
    login_password = driver.find_element_by_xpath("/html/body/div[3]/div/div/table/tbody/tr/td/form/div/div[2]/dl[1]/dd[2]/input")
    login_password.send_keys(args["51_form_password"])

    login_btn = driver.find_element_by_xpath("/html/body/div[3]/div/div/table/tbody/tr/td/form/div/div[2]/p[1]/input")
    login_btn.click()


login()

event_id = "3027"
event_url = f"https://51stregiment.com/forum/index.php?topic={event_id}.0"
driver.get(event_url)
event_id = driver.find_element_by_xpath("/html/body/div[3]/div/div/table/tbody/tr/td/div[1]/div[2]/div/ul/li[2]/form/input[2]")
admin_event_id = event_id.get_attribute("value")

admin_event_url = driver.get(f"https://51stregiment.com/forum/index.php?action=admin_register_event;event={admin_event_id}")
checkbox_form = driver.find_element_by_xpath("/html/body/div[3]/div/div/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td[1]/form")

name_list = checkbox_form.text.split(sep="\n")[4:]
name_list = [x.strip() for x in name_list]

checkbox_list = checkbox_form.find_elements_by_tag_name("input")
checkbox_list = checkbox_list[3:]

my_index = name_list.index("Cultiststeve")
print(f"Found name at {my_index}")
checkbox_list[my_index].click()

# driver.switch_to.frame(checkbox_form)

# my checkbox is
# my_checkbox = driver.find_element(By.XPATH, """//*[@id="checkm_1092"]//preceding-sibling::input[1]""")
# my_checkbox = driver.find_element(By.XPATH, """//*[@id="checkm_1092"]""")

# below_my_checkbox = my_checkbox.find_element(with_tag_name("input").below(my_checkbox))

# print(my_checkbox)

driver.save_screenshot("screenshot.png")
driver.quit()
