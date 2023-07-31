"""
ToUI with SQL User Database

ToUI can be easily used with SQL database for:

- User authentication
- Storing user data in database


This example uses the HTML file "test8.html":

.. code-block:: html

   <!DOCTYPE html>
   <html lang="en">
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Document</title>
   </head>
   <body>
       <h1>Sign in users:</h1>
       <input id="username"/>
       <input id="password"/>
       <button id="sign-in">Sign in</button>
       <button id="sign-up">Sign up</button>
       <p id="output"></p>
   </body>
   </html>

Python code:
"""
import sys
sys.path.append("..")
import os
from toui import Website, Page

app = Website(__name__, assets_folder="assets", secret_key="some text")
SQL_URI = f"sqlite:///{os.getcwd()}/.test.db" # Change this value to match your SQL database URI
app.add_user_database_using_sql(SQL_URI, other_columns=["age"]) # Connects to sql database.
main_pg = Page(html_file="assets/test8.html", url="/")

def sign_in():
    pg = app.get_user_page()
    username = pg.get_element("username").get_value()
    password = pg.get_element("password").get_value()
    pg.get_element("output").set_content("loading")
    success = app.signin_user(username=username, password=password)
    if success:
        age = app.get_current_user_data("age")
        pg.get_element("output").set_content(f"Signed in successfully. Age of user: {age}")
    else:
        pg.get_element("output").set_content("Sign in failed")

def sign_up():
    pg = app.get_user_page()
    username = pg.get_element("username").get_value()
    password = pg.get_element("password").get_value()
    pg.get_element("output").set_content("loading")
    success = app.signup_user(username=username, password=password)
    if success:
        app.signin_user(username=username, password=password)
        value_added = app.set_current_user_data("age", 20)
        pg.get_element("output").set_content(f"Signed up successfully. Age added: {value_added}")
    else:
        pg.get_element("output").set_content("Sign up failed")

def set_age():
    pg = app.get_user_page()
    age = pg.get_element("age").get_value()
    app.set_current_user_data("age", age)
    pg.get_element("age-output").set_content(f"Age set to {age}")

def get_age():
    pg = app.get_user_page()
    age = app.get_current_user_data("age")
    pg.get_element("age-output").set_content(f"Age is {age}")

main_pg.get_element("sign-in").onclick(sign_in)
main_pg.get_element("sign-up").onclick(sign_up)
main_pg.get_element("set-age").onclick(set_age)
main_pg.get_element("get-age").onclick(get_age)


app.add_pages(main_pg)

if __name__ == '__main__':
    app.run()

        