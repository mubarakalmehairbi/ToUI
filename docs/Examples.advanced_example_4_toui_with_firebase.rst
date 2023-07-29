ToUI with Firebase
==================

ToUI can be used with Firebase. Create a Firebase app to use this example. In this example, ToUI is used with Firebase for:

- User authentication
- Stroing user data in database
- File storage
- File retrieval


This example uses the HTML file "test7.html":

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
       <h1>Upload files:</h1>
       <input type="file" id="file"/>
       <button id="get-file">Download uploaded file</button>
       <p id="output2"></p>
   </body>
   </html>

Python code:

.. code-block:: python

   import os
   from toui import Website, Page
   
   app = Website(__name__, assets_folder="assets", secret_key="some text")
   app.add_firebase(".my_firebase_credentials.json") # You can get this file from your firebase project settings
   app.add_user_database_using_firebase() # Connects to firestore database. Make sure that you created one in Firebase.
   BUCKET_NAME = "test-14583.appspot.com" # Change this value to match your bucket name in Firebase Storage
   
   main_pg = Page(html_file="assets/test7.html", url="/")
   
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
   
   
   def store_file():
       pg = app.get_user_page()
       file = pg.get_element("file").get_files()[0]
       with open(".test_file", "w") as f:
           file.save(f)
       app.store_file_using_firebase(destination_path=f"{app.get_current_user_id()}/test_file", file_path=".test_file", bucket_name=BUCKET_NAME)
       pg.get_element("output2").set_content("File stored")
   
   def retrieve_file():
       pg = app.get_user_page()
       if os.path.exists(".new_test_file"):
           raise Exception(".new_test_file already exists")
       app.get_file_from_firebase(source_path=f"{app.get_current_user_id()}/test_file", new_file_path=".new_test_file", bucket_name=BUCKET_NAME)
       with open(".new_test_file", "r") as f:
           pg.get_element("output2").set_content("Downloaded file content: " + f.read())
   
   
   main_pg.get_element("sign-in").onclick(sign_in)
   main_pg.get_element("sign-up").onclick(sign_up)
   main_pg.get_element("file").on("change", store_file)
   main_pg.get_element("get-file").onclick(retrieve_file)
   
   app.add_pages(main_pg)
   
   if __name__ == '__main__':
       app.run()
   
           
   