Basic example of a desktop app
==============================



.. code-block:: python

   from toui import Page, DesktopApp
   
   
   # create the app
   app = DesktopApp("MyDesktopApp", assets_folder="assets")
   
   # create a page
   main_pg = Page(html_file="assets/test1.html")
   
   # create a function and add it to the page
   def printValue():
       print("value")
   
   button = main_pg.get_element('print-button') # 'print-button' is an id of a <button>
   button.onclick(printValue)
   
   # add the page to the app
   app.add_pages(main_pg)
   
   # run the app
   if __name__ == "__main__":
       app.run()
   