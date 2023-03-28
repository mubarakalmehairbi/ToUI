"""
Basic example of a website
"""
from toui import Page, Website


# create website
app = Website(__name__, assets_folder="assets", secret_key="some text")

# create page
main_pg = Page(html_file="assets/test1.html", url="/")

# create a function and add it to the page
def printValue():
    print("value")

button = main_pg.get_element('print-button') # 'print-button' is an id of a <button>
button.onclick(printValue)

# add the page to the website
app.add_pages(main_pg)

# run
if __name__ == "__main__":
    app.run(debug=True)