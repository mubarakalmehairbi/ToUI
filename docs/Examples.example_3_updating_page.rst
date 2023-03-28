Dynamic web page
================



.. code-block:: python

   from toui import Page, Website
   
   
   # create website
   app = Website(__name__, assets_folder="assets", secret_key="some text")
   
   # create page
   main_pg = Page(html_file="assets/test3.html", url="/")
   
   # create a function and add it to the page
   def addValues():
       page = app.get_user_page()
       input1 = page.get_element("input-1").get_value()
       input2 = page.get_element("input-2").get_value()
       result = float(input1) + float(input2)
       page.get_element('output').set_value(result)
   
   add_button = main_pg.get_element('add-button') # 'add-button' is an id of a <button>
   add_button.onclick(addValues)
   
   # add the page to the website
   app.add_pages(main_pg)
   
   # run
   if __name__ == "__main__":
       app.run(debug=True)
   