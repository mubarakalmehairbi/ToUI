"""
A module for containing classes that help in organizing the apps.
"""

import flask
from copy import copy


class ToUIBlueprint(flask.Blueprint):
    """
    A class that inherits `flask.Blueprint`.

    The difference between this class and `flask.Blueprint` is that you can add `Page`
    objects to this class. To learn how to use blueprints, check `flask's` documentation
    https://flask.palletsprojects.com/.

    Examples
    --------

    Creating a blueprint:

    >>> from toui import ToUIBlueprint
    >>> blueprint = ToUIBlueprint("Blueprint", __name__)

    Adding a `Page` to a blueprint:

    >>> from toui import Page
    >>> page = Page(html_str="<h1>This page is part of a blueprint</h1>", url="/")
    >>> blueprint.add_pages(page)

    Creating a `Website` and adding the blueprint to it:

    >>> from toui import Website
    >>> app = Website(__name__)
    >>> app.register_toui_blueprint(blueprint)

    See Also
    --------
    flask.Blueprint

    """
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        args
            `flask.Blueprint` arguments.
        kwargs
            `flask.Blueprint` keyword arguments.
        """
        super(ToUIBlueprint, self).__init__(*args, **kwargs)
        self.pages = []

    def add_pages(self, *pages, do_copy=False):
        """Adds pages to the blueprint.

        Parameters
        ----------
        pages: list(Page)
            List of 'Page' objects.

        """
        for page in pages:
            if do_copy:
                page = copy(page)
            self.pages.append(page)

    def register_toui_blueprint(self, blueprint, **options):
        """
        Registers a `ToUIBlueprint` object. It is similar to `flask.Blueprint.register_blueprint`.

        Parameters
        ----------
        blueprint: toui.structure.ToUIBlueprint

        options
            Same as `flask.Blueprint.register_blueprint` `options` parameter.

        See Also
        --------
        toui.structure.ToUIBlueprint
        flask.Blueprint.register_blueprint

        """
        self.add_pages(*blueprint.pages)
        self.register_blueprint(blueprint, **options)


if __name__ == "__main__":
    import doctest
    doctest.testmod()