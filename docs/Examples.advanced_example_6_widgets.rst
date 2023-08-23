Create widgets using ToUI
=========================

**Note**: make sure to have some background in object-oriented programming (classes), otherwise this example
might be confusing.

When creating an app, sometimes you find that you need to duplicate some HTML code in various
places. This is sometimes inconvenient, but one of the solutions is to create a "widget". A "widget"
here means a shortcut for a group of HTML elements. For example, we can create a widget for a table:

.. code-block:: python
   
   from toui import Element
   
   class TableWidget:
   
       def __init__(self):
           # Create an `Element` object inside the widget
           self.element = Element()
           self.element.from_str(
           """
           <table>
               <tr>
                   <th>Column A</th>
                   <th>Column B</th>
               </tr>
               <tr>
                   <td>1</td>
                   <td>12</td>
               </tr>
               <tr>
                   <td>21</td>
                   <td>22</td>
               </tr>
           </table>
           """
           )

When you create an instance of `TableWidget`, a string containing the table HTML element is stored in
`TableWidget.element`. However, the purpose of creating a widget is not only to store some HTML
code, but to make it easier to edit the HTML code. For example, if we want to frequently update the data
inside the table, we can create a new method inside `TableWidget`:

.. code-block:: python
   
   from toui import Element
   
   class TableWidget:
   
       def __init__(self):
           # Create an `Element` object inside the widget
           self.element = Element()
           self.element.from_str(
           """
           <table>
           </table>
           """
           )
   
       def from_list(self, table_list):
           """Update the data inside the table using a Python list"""
           self.element.set_content("")
           headers = table_list[0]
           headers_element = Element("tr")
           for header in headers:
               headers_element.add_content(f"<th>{header}</th>")
           self.element.add_content(headers_element)
           for row in table_list[1:]:
               row_element = Element("tr")
               for value in row:
                   row_element.add_content(f"<td>{value}</td>")
               self.element.add_content(row_element)

The method `from_list` will take the data from a Python list and insert it into the table. This
is convenient because you do not need to write the Python code that will insert data to the
table everytime since you can just call the method `from_list`.

The preferred method of creating a widget is to create a class and create an attribute inside it
called `element`. The attribute `element` is an object of the `Element` class. Another method
is to create a class that inherits the `Element` class:

.. code-block:: python

   class TableWidget2(Element):
   
       def __init__(self):
           # The widget itself is an instance of `Element` class.
           super().__init__()
           self.from_str(
           """
           <table>
           </table>
           """
           )
   
       def from_list(self, table_list):
           self.set_content("")
           headers = table_list[0]
           headers_element = Element("tr")
           for header in headers:
               headers_element.add_content(f"<th>{header}</th>")
           self.add_content(headers_element)
           for row in table_list[1:]:
               row_element = Element("tr")
               for value in row:
                   row_element.add_content(f"<td>{value}</td>")
               self.add_content(row_element)


However, in the second approach, you might find some difficulty in creating a widget from an already
existent HTML code. For example, if a `<table>` element already exists in the HTML document and you
want to convert it to a widget, the second approach might not be helpful.


Below is a complete example that creates widgets. The example uses the HTML file "test9.html":

.. code-block:: html

   <!DOCTYPE html>
   <html lang="en">
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Document</title>
   </head>
   <body>
       <h1>Table 1</h1>
       <button id="add-table-1">Add Table 1</button>
       <div id="table-1"></div>
       <h1>Table 2</h1>
       <button id="add-table-2">Add Table 2</button>
       <div id="table-2"></div>
   </body>
   </html>

The example Python code:

.. code-block:: python

   import sys
   sys.path.append("..")
   from toui import Element, Page, Website
   
   
   class TableWidget:
   
       def __init__(self):
           # Create an `Element` object inside the widget
           self.element = Element()
           self.element.from_str(
           """
           <table>
           </table>
           """
           )
   
       def from_list(self, table_list):
           self.element.set_content("")
           headers = table_list[0]
           headers_element = Element("tr")
           for header in headers:
               headers_element.add_content(f"<th>{header}</th>")
           self.element.add_content(headers_element)
           for row in table_list[1:]:
               row_element = Element("tr")
               for value in row:
                   row_element.add_content(f"<td>{value}</td>")
               self.element.add_content(row_element)
   
   
   class TableWidget2(Element):
   
       def __init__(self):
           # The widget itself is an instance of `Element` class.
           super().__init__()
           self.from_str(
           """
           <table>
           </table>
           """
           )
   
       def from_list(self, table_list):
           self.set_content("")
           headers = table_list[0]
           headers_element = Element("tr")
           for header in headers:
               headers_element.add_content(f"<th>{header}</th>")
           self.add_content(headers_element)
           for row in table_list[1:]:
               row_element = Element("tr")
               for value in row:
                   row_element.add_content(f"<td>{value}</td>")
               self.add_content(row_element)
   
   
   # Create an app
   app = Website(name=__name__, assets_folder="assets", secret_key="some long string")
   
   # Create a page
   pg = Page("assets/test9.html", url="/")
   
   # Create a function that adds a table to the page
   def add_table1():
       pg = app.get_user_page()
       # Create a table widget
       table_widget = TableWidget()
       # Add data to the table widget using `from_list` method
       table_widget.from_list([
           ["Column A", "Column B"],
           ["1", "2"],
           ["3", "4"]
       ])
       pg.get_element("table-1").set_content(table_widget.element)
   
   
   # Create a function that adds another type of table to the page
   def add_table2():
       pg = app.get_user_page()
       # Create a table widget
       table_widget = TableWidget2()
       # Add data to the table widget using `from_list` method
       table_widget.from_list([
           ["Column A", "Column B"],
           ["1", "2"],
           ["3", "4"]
       ])
       pg.get_element("table-2").set_content(table_widget)
   
   
   # Call a function when the button `add-table-1` is clicked
   pg.get_element("add-table-1").onclick(add_table1)
   # Call a function when the button `add-table-2` is clicked
   pg.get_element("add-table-2").onclick(add_table2)
   
   # Add the page to the app
   app.add_pages(pg)
   
   # Run
   if __name__ == "__main__":
       app.run(debug=True)
   
   
   