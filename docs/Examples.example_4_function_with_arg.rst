Adding a function with arguments
================================



.. code-block:: python

   from toui import Page, Website
   
   
   # create website
   app = Website(__name__, assets_folder="assets", secret_key="some text")
   
   # create page
   main_pg = Page(html_file="assets/test2.html", url="/")
   
   # create a function and add it to the page
   def printValue(value):
       print(value)
   
   button_1 = main_pg.get_element("print-button1") # 'print-button1' is an id of a <button>
   button_1.onclick(printValue, 1)
   button_2 = main_pg.get_element("print-button2") # 'print-button1' is an id of a <button>
   button_2.onclick(printValue, 2)
   
   # add the page to the website
   app.add_pages(main_pg)
   
   # run
   if __name__ == "__main__":
       app.run(debug=True)
   