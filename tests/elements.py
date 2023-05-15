import unittest
import sys
sys.path.append("..")
from toui import Element

def example_func(arg1, args2):
    pass

class MyTestCase(unittest.TestCase):
    def test_element_creation(self):
        element = Element("button")
        self.assertEqual(str(element), "<button></button>")
    def test_element_attrs(self):
        element = Element("div")
        element.onclick(example_func, 1, 2)
        element.set_id("example-id")
        element.set_attr("class", "example-class")
        self.assertEqual(str(element),
                         '<div class="example-class" id="example-id" onclick=\'example_func("1","2")\'></div>')
    def test_element_content(self):
        element = Element("p")
        element.set_content("some text")
        self.assertEqual(str(element), '<p>some text</p>')
    def test_style_attr(self):
        element = Element("p")
        element.set_style_property("width", "100%")
        element.set_style_property("height", "1000px")
        self.assertEqual(str(element), '<p style="width: 100%;height: 1000px;"></p>')
        width = element.get_style_property("width")
        self.assertEqual(width, "100%")


if __name__ == '__main__':
    unittest.main()
