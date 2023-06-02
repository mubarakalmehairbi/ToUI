ToUI with JavaScript
====================

ToUI does not restrict you from using JavaScript code. It can also allow you to call Python functions
from JavaScript. However, note that ToUI creates some JavaScript functions that should not be overwritten.
These functions start with an underscore.

This example uses the HTML file "test5.html":

.. code-block:: html

   <!DOCTYPE html>
   <html lang="en">
   <head>
       <meta charset="UTF-8">
       <meta http-equiv="X-UA-Compatible" content="IE=edge">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Document</title>
   </head>
   <body>
       <button onclick="javascriptFunction()">Call JavaScript Function</button>
       <script>
           function javascriptFunction() {
               pythonFunction()
           }
       </script>
   </body>
   </html>

Python code:

.. code-block:: python

   from toui import Website, Page
   
   # create website
   app = Website(__name__, assets_folder="assets", secret_key="some text")
   
   # create page
   main_pg = Page(html_file="assets/test5.html", url="/")
   
   # create a function and add it to the page
   def pythonFunction():
       print("A Python function was called from JavaScript.")
   
   main_pg.add_function(pythonFunction)
   
   # add the page to the website
   app.add_pages(main_pg)
   
   # run
   if __name__ == "__main__":
       app.run(debug=True)
   