import unittest
from toui import Page

class MyTestCase(unittest.TestCase):
    def test_page(self):
        page = Page(html_str="<button></button>")
        self.assertEqual(str(page), "<html><button></button></html>")
        button = page.get_elements(tag_name="button")[0]
        self.assertEqual(str(button), "<button></button>")


if __name__ == '__main__':
    unittest.main()