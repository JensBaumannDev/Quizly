from pathlib import Path

import yaml
from django.conf import settings
from django.test import SimpleTestCase


class ApiDocumentationTests(SimpleTestCase):
    expected_operations = {
        "/register/": {"post": {"201", "400", "500"}},
        "/login/": {"post": {"200", "401", "500"}},
        "/logout/": {"post": {"200", "401", "500"}},
        "/token/refresh/": {"post": {"200", "401", "500"}},
        "/quizzes/": {
            "get": {"200", "401", "500"},
            "post": {"201", "400", "401", "500"},
        },
        "/quizzes/{id}/": {
            "get": {"200", "401", "403", "404", "500"},
            "patch": {"200", "400", "401", "403", "404", "500"},
            "delete": {"204", "401", "403", "404", "500"},
        },
    }

    def parse_schema_response(self):
        response = self.client.get("/swagger.yaml")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/yaml; charset=utf-8")
        return yaml.safe_load(response.content)

    def assert_documented_operations(self, schema):
        for path, operations in self.expected_operations.items():
            with self.subTest(path=path):
                self.assertIn(path, schema["paths"])
            self.assert_operation_responses(schema["paths"][path], operations)

    def assert_operation_responses(self, path_schema, operations):
        documented_methods = set(path_schema) - {"parameters"}
        self.assertEqual(documented_methods, set(operations))
        for method, status_codes in operations.items():
            with self.subTest(method=method):
                self.assertIn(method, path_schema)
                responses = set(path_schema[method]["responses"])
                self.assertEqual(responses, status_codes)

    def test_serves_swagger_ui(self):
        response = self.client.get("/swagger/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quizly API")

    def test_serves_complete_yaml_schema(self):
        schema = self.parse_schema_response()
        self.assertEqual(schema["swagger"], "2.0")
        self.assertEqual(schema["basePath"], "/api")
        self.assertEqual(schema["info"]["title"], "Quizly API")
        self.assert_documented_operations(schema)

    def test_static_schema_matches_documented_operations(self):
        schema_path = Path(settings.BASE_DIR) / "schema.yml"
        self.assertTrue(schema_path.is_file())
        schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        self.assert_documented_operations(schema)
