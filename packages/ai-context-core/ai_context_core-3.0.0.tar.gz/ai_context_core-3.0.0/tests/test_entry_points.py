import unittest
import ast
from ai_context_core.analyzer import ast_utils


class TestEntryPoints(unittest.TestCase):
    def test_main_guard(self):
        code = """
if __name__ == "__main__":
    print("Main")
"""
        tree = ast.parse(code)
        result = ast_utils.is_entry_point(tree)
        self.assertTrue(result["is_entry_point"])
        self.assertEqual(result["type"], "main_guard")

    def test_qgis_plugin(self):
        code = """
def classFactory(iface):
    return MyPlugin(iface)
"""
        tree = ast.parse(code)
        result = ast_utils.is_entry_point(tree)
        self.assertTrue(result["is_entry_point"])
        self.assertEqual(result["type"], "qgis_plugin")

    def test_click_cli(self):
        code = """
import click

@click.command()
def cli():
    pass
"""
        tree = ast.parse(code)
        result = ast_utils.is_entry_point(tree)
        self.assertTrue(result["is_entry_point"])
        self.assertEqual(result["type"], "click_cli")

    def test_flask_app(self):
        code = """
from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "Hello"
"""
        tree = ast.parse(code)
        result = ast_utils.is_entry_point(tree)
        self.assertTrue(result["is_entry_point"])
        self.assertEqual(result["type"], "flask_app")

    def test_fastapi_app(self):
        code = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
"""
        tree = ast.parse(code)
        result = ast_utils.is_entry_point(tree)
        self.assertTrue(result["is_entry_point"])
        self.assertEqual(result["type"], "fastapi_app")

    def test_not_entry_point(self):
        code = """
def normal_function():
    pass
"""
        tree = ast.parse(code)
        result = ast_utils.is_entry_point(tree)
        self.assertFalse(result["is_entry_point"])
        self.assertIsNone(result["type"])

    def test_django_wsgi(self):
        code = "application = get_wsgi_application()"
        tree = ast.parse(code)
        result = ast_utils.is_entry_point(tree)
        self.assertTrue(result["is_entry_point"])
        self.assertEqual(result["type"], "django_app")

    def test_django_settings(self):
        code = "INSTALLED_APPS = ['django.contrib.admin']"
        tree = ast.parse(code)
        result = ast_utils.is_entry_point(tree)
        self.assertTrue(result["is_entry_point"])
        self.assertEqual(result["type"], "django_settings")

    def test_django_urls(self):
        code = "urlpatterns = [path('admin/', admin.site.urls)]"
        tree = ast.parse(code)
        result = ast_utils.is_entry_point(tree)
        self.assertTrue(result["is_entry_point"])
        self.assertEqual(result["type"], "django_urls")


if __name__ == "__main__":
    unittest.main()
