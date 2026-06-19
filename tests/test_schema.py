import copy
import unittest

from promptfloater.schema import ValidationError, validate_document


def valid_document():
    return {
        "categories": [
            {
                "id": "cat-1",
                "name": "工具",
                "items": [{"id": "item-1", "content": "hello"}],
            }
        ]
    }


class SchemaTests(unittest.TestCase):
    def test_normalizes_valid_document_without_mutating_input(self):
        source = valid_document()
        original = copy.deepcopy(source)

        result = validate_document(source)

        self.assertEqual(source, original)
        self.assertEqual(result["schema_version"], 1)
        item = result["categories"][0]["items"][0]
        self.assertEqual(item["desc"], "")
        self.assertFalse(item["fav"])

    def test_preserves_html_like_strings_as_plain_data(self):
        source = valid_document()
        source["categories"][0]["name"] = '"><img src=x onerror=alert(1)>'
        source["categories"][0]["items"][0]["content"] = "<script>alert(1)</script>"

        result = validate_document(source)

        self.assertEqual(result["categories"][0]["name"], source["categories"][0]["name"])
        self.assertEqual(result["categories"][0]["items"][0]["content"], source["categories"][0]["items"][0]["content"])

    def test_rejects_non_object_root(self):
        with self.assertRaisesRegex(ValidationError, "根节点"):
            validate_document([])

    def test_rejects_non_list_categories(self):
        with self.assertRaisesRegex(ValidationError, "categories"):
            validate_document({"categories": "bad"})

    def test_rejects_duplicate_category_ids(self):
        source = valid_document()
        source["categories"].append(copy.deepcopy(source["categories"][0]))
        with self.assertRaisesRegex(ValidationError, "分类 ID 重复"):
            validate_document(source)

    def test_rejects_duplicate_item_ids(self):
        source = valid_document()
        source["categories"][0]["items"].append({"id": "item-1", "content": "two"})
        with self.assertRaisesRegex(ValidationError, "提示词 ID 重复"):
            validate_document(source)

    def test_rejects_missing_content(self):
        source = valid_document()
        del source["categories"][0]["items"][0]["content"]
        with self.assertRaisesRegex(ValidationError, "content"):
            validate_document(source)

    def test_rejects_overlong_fields(self):
        source = valid_document()
        source["categories"][0]["name"] = "x" * 121
        with self.assertRaisesRegex(ValidationError, "name"):
            validate_document(source)

    def test_rejects_too_many_categories(self):
        source = {"categories": []}
        for index in range(101):
            source["categories"].append({"id": f"c{index}", "name": "C", "items": []})
        with self.assertRaisesRegex(ValidationError, "分类数量"):
            validate_document(source)


if __name__ == "__main__":
    unittest.main()
