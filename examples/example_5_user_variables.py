"""
User-specific variables
"""
from toui import Page, Website


# create website
app = Website(__name__, assets_folder="assets", secret_key="some text")

# create page
main_pg = Page(html_file="assets/test4.html", url="/")

# create a function and add it to the page
def saveData():
    page = app.get_user_page()
    input_element = page.get_element("input")
    data = input_element.get_value()
    input_element.set_value("")
    app.user_vars['data_saved'] = data

def loadData():
    data = app.user_vars['data_saved']
    page = app.get_user_page()
    data = page.get_element("output").set_content(data)

save_button = main_pg.get_element("save-button") # 'save-button' is an id of a <button>
save_button.onclick(saveData)
load_button = main_pg.get_element("load-button") # 'load-button' is an id of a <button>
load_button.onclick(loadData)

# add the page to the website
app.add_pages(main_pg)

# run
if __name__ == "__main__":
    app.run(debug=True)