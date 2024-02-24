import unittest
from pathlib import Path

import yaml

from ai_code_reviewer.base import Reviewer, ProgrammingPrincipleChecker, ProgrammingPrinciple, FilePatchReview, \
    FilePatchComment
from ai_code_reviewer.utils import add_line_numbers


class TestAddLineNumbers(unittest.TestCase):
    def test_empty_string(self):
        self.assertEqual(add_line_numbers(""), "")

    def test_single_line(self):
        self.assertEqual(add_line_numbers("Hello, World!"), "0: Hello, World!\n")

    def test_multiple_lines(self):
        input_text = "Hello,\nWorld!"
        expected_output = "0: Hello,\n1: World!\n"
        self.assertEqual(add_line_numbers(input_text), expected_output)


class TestReviewer(Reviewer):
    async def review_file_patch(self, patch: str) -> FilePatchReview:
        return FilePatchReview(
            comments=[
                FilePatchComment(
                    line_number=3,
                    comment="test_review"
                )
            ]
        )


class MyTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_reviewer = TestReviewer()

    async def test_reviewer(self):
        test_changes = "Some test changes"
        patch_review = await self.test_reviewer.review_file_patch(test_changes)
        self.assertEqual(len(patch_review.comments), 1)
        self.assertEqual(patch_review.comments[0].line_number, 3)
        self.assertEqual(patch_review.comments[0].comment, "test_review")


class TestProgrammingPrincipleChecker(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        principle_path = Path(__file__).parents[1] / ".coding_principles" / "single_responsibility.yaml"
        with open(principle_path, "r") as file:
            programming_principle_dict = yaml.safe_load(file)
            programming_principle = ProgrammingPrinciple(**programming_principle_dict)
        self.reviewer = ProgrammingPrincipleChecker(
            programming_principle=programming_principle
        )

    async def test_review(self):
        test_patch = """@@ -10,20 +15,39 @@ class ReviewComment(BaseModel):
+ class FileManager:
+     def __init__(self, filename):
+         self.path = Path(filename)
+
+     def read(self, encoding="utf-8"):
+         return self.path.read_text(encoding)
+
+     def write(self, data, encoding="utf-8"):
+         self.path.write_text(data, encoding)
+
+     def compress(self):
+         with ZipFile(self.path.with_suffix(".zip"), mode="w") as archive:
+             archive.write(self.path)
+
+     def decompress(self):
+         with ZipFile(self.path.with_suffix(".zip"), mode="r") as archive:
+             archive.extractall()
"""
        reviews = await self.reviewer.review_file_patch(test_patch)
        self.assertGreater(len(reviews.comments), 0)
