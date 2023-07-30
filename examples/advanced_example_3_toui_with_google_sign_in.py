"""
ToUI with Google sign in

ToUI can be used with Google sign in. This example shows how to use Google sign in with ToUI.
Make sure to create a Google app first. Also, add the following as an authorized redirect URI to your Google app:
``https://<your-domain>/toui-google-sign-in``

One way to create a Google app is through Google Firebase. Perhaps check it out. Note that you will need to access
Google API console nevertheless to enter the authorized redirect URI: ``https://<your-domain>/toui-google-sign-in``

This example uses the HTML file "test6.html":

.. code-block:: html

   <!DOCTYPE html>
   <html lang="en">
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Document</title>
   </head>
   <body>
       <button id="sign-in"><img width="200px" src="./google_button.png"></img></button>
       <p id="user-info"></p>
   </body>
   </html>

Python code:
"""
import sys
sys.path.append("..")
import os
from toui import Website, Page

# Get these from your google app.
GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = os.environ['GOOGLE_CLIENT_SECRET']

# Create app
app = Website(__name__, assets_folder="assets", secret_key="some secret key")
app.add_user_database_using_sql(f"sqlite:///{os.getcwd()}/.user_database.db")

# Create pages
pg = Page(html_file="assets/test6.html", url="/")

# Create functions that will be called from HTML
def get_user_info():
    pg = app.get_user_page()
    if app.is_signed_in():
        pg.get_element("user-info").set_content(f"User: {app.get_current_user_data('username')}")

def sign_in():
    """Sign in using Google."""
    app.sign_in_using_google(client_id=GOOGLE_CLIENT_ID,
                             client_secret=GOOGLE_CLIENT_SECRET,
                             after_auth_url="/")

# Connect functions to elements
pg.get_body_element().on("load", get_user_info)
pg.get_element("sign-in").onclick(sign_in)

# Add pages to app
app.add_pages(pg)

if __name__ == '__main__':
    app.run()