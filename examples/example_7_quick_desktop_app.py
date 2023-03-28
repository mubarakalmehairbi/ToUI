"""
Quick desktop app
"""

from toui import quick_desktop_app


app = quick_desktop_app(html_str="<h1>Title</h1>")

if __name__ == "__main__":
    app.run()