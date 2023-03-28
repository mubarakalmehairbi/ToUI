"""
Quick website
"""
from toui import quick_website


app = quick_website(html_str="<h1>Title</h1>")

if __name__ == "__main__":
    app.run(debug=True)