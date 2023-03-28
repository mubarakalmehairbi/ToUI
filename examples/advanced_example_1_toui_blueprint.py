"""
ToUI Blueprints

`ToUI.Blueprint` is a class that inherits `flask.Blueprint` and adds more methods to it.
The difference between this class and `flask.Blueprint` is that you can add `Page`
objects to this class. To learn how to use blueprints, check `flask's` documentation
https://flask.palletsprojects.com/.
"""
from toui import Page, Website, ToUIBlueprint

# create a blueprint
blueprint = ToUIBlueprint("Blueprint", __name__)
page = Page(html_str="<h1>This page is part of a blueprint</h1>", url="/")
blueprint.add_pages(page)

# create a website and add the blueprint to it:
app = Website(__name__, secret_key="some text")
app.register_toui_blueprint(blueprint, url_prefix="/blueprint")

# create a main page
main_page = Page(html_str="<a href='/blueprint'>Go to blueprint page<a/>", url="/")
app.add_pages(main_page)

# run
if __name__ == "__main__":
    app.run(debug=True)