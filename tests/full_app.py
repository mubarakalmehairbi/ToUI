import sys
import os
import time
sys.path.append("..")
from toui import DesktopApp, Website, Page
from toui._helpers import show_debug

show_debug(True)

##################################################
#
#   App creation and configuration
#
##################################################

#app = Website(__name__, assets_folder="assets")
app = DesktopApp(__name__, assets_folder="assets")
app.add_restriction('username', 'p123')
app.add_user_database(f"sqlite:///{os.getcwd()}/.user_database.db")
app.user_vars['my default variable'] = "default value"

##################################################
#
#   Pages
#
##################################################

home_page = Page(html_file="assets/full_app.html", url="/", title="Home")
home_page.window_defaults['width'] = 800
page_2 = Page(html_file="assets/full_app_pg_2.html", url="/pg-2")

def change_text():
    page = app.get_user_page()
    page.get_element("text").set_content("The text has changed")


def download_file():
    app.download(__file__)


def new_page_same_tab(new):
    app.open_new_page("/pg-2", new=new)


def username_exists():
    pg = app.get_user_page()
    username = pg.get_element("username").get_value()
    exists = app.username_exists(username)
    output = pg.get_element("check-username-output")
    if exists:
        output.set_content("Username exists")
    else:
        output.set_content("Username does not exist")


def sign_up():
    pg = app.get_user_page()
    username = pg.get_element("username").get_value()
    password = pg.get_element("password").get_value()
    success = app.signup_user(username=username, password=password)
    output = pg.get_element("sign-up-output")
    if success:
        output.set_content("Signing up was successful")
    else:
        output.set_content("Signing up failed")
    update_current_user()


def sign_in():
    pg = app.get_user_page()
    username = pg.get_element("username").get_value()
    password = pg.get_element("password").get_value()
    success = app.signin_user(username=username, password=password)
    output = pg.get_element("sign-in-output")
    if success:
        output.set_content("Signing in was successful")
    else:
        output.set_content("Signing in failed")
    update_current_user()


def sign_out():
    app.signout_user()
    update_current_user()


def update_current_user():
    pg = app.get_user_page()
    user = app.get_current_user()
    output = pg.get_element("current-user")
    if user:
        output.set_content(user.username)
    else:
        output.set_content(None)


def add_user_var():
    pg = app.get_user_page()
    key = pg.get_element("user-var-key").get_value()
    value = pg.get_element("user-var-value").get_value()
    app.user_vars[key] = value


def display_user_vars():
    user_vars = ""
    for key, value in app.user_vars.items():
        user_vars += f"{key}: {value}\n"
    app.get_user_page().get_element("user-vars").set_content(user_vars)


def upload_file():
    pg = app.get_user_page()
    files = pg.get_element("file-upload").get_files()
    for file in files:
        name = file.name
        if os.path.exists(name):
            print("File already exists")
            return
        with open(name, "w") as stream:
            file.save(stream)
    pg.get_element("file-upload-status").set_content(f"File '{name}' uploaded.")


def change_selected():
    pg = app.get_user_page()
    option = pg.get_element("colors").get_selected()
    color = option.get_content()
    pg.get_element("selected").set_content(f"Selected color is {color}")


def get_element_selector():
    pg = app.get_user_page()
    element_selector = pg.get_element("get-selector").get_selector()
    pg.get_element("display-selector").set_content(element_selector)


def get_unique_selector():
    pg = app.get_user_page()
    element_selector = pg.get_elements(name="get-unique-selector")[0].get_unique_selector()
    pg.get_element("display-selector").set_content(element_selector)


def get_itself(element):
    element.set_content("success")


def quick_click():
    pg = app.get_user_page()
    count = int(pg.get_element("click-count").get_content()) + 1
    pg.get_element("click-count").set_content(count)
    files = pg.get_element("hidden-files-input").get_files()
    time.sleep(0.5)


def resize(w, h):
    window = app.get_user_page().get_window()
    if window:
        window.resize(w, h)


home_page.on_url_request(change_text)
home_page.get_body_element().on('load',resize , 800, 800, quotes=False)
home_page.get_element("new-page-same").onclick(new_page_same_tab, False, quotes=False)
home_page.get_element("new-page-diff").onclick(new_page_same_tab, True, quotes=False)
home_page.get_element("download").onclick(download_file)
home_page.get_element("check-username").onclick(username_exists)
home_page.get_element("sign-up").onclick(sign_up)
home_page.get_element("sign-in").onclick(sign_in)
home_page.get_element("sign-out").onclick(sign_out)
home_page.get_element("add-user-var").onclick(add_user_var)
home_page.get_element("display-user-vars").onclick(display_user_vars)
home_page.get_element("file-upload").on("change", upload_file)
home_page.get_element("colors").on("change", change_selected)
home_page.get_element("get-selector").onclick(get_element_selector)
home_page.get_elements(name="get-unique-selector")[0].onclick(get_unique_selector)
home_page.get_element("get-itself").onclick(get_itself, return_itself=True)
home_page.get_element("quick-click").onclick(quick_click)
home_page.get_element("resize").onclick(resize, 1000, 1000, quotes=False)


def get_current_user():
    pg = app.get_user_page()
    current_user = app.get_current_user()
    if current_user:
        username = current_user.username
    else:
        username = "no user signed in"
    pg.get_element("display-user").set_content(username)


def return_to_home():
    app.open_new_page("/")


page_2.on_url_request(get_current_user)
page_2.get_element("return").onclick(return_to_home)



app.add_pages(home_page, page_2)
if __name__ == "__main__":
    app.run()