import unittest
from pathlib import Path

from ai_code_reviewer.containers import Container, AppConfig
from ai_code_reviewer.review import FileDiffReview, \
    FileDiffComment
from ai_code_reviewer.reviewers.base import Reviewer
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
    async def review_file_diff(self, diff: str) -> FileDiffReview:
        return FileDiffReview(
            comments=[
                FileDiffComment(
                    line_number=3,
                    comment="test_review",
                    suggestion="test suggestion",
                    implementation="test implementation",
                    citation_from_principle="test citation",
                    how_citation_violated="test violation",
                    on_the_other_hand="test opposition",
                    is_violating_principle=True
                )
            ]
        )


class MyTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_reviewer = TestReviewer()

    async def test_reviewer(self):
        test_changes = "Some test changes"
        review = await self.test_reviewer.review_file_diff(test_changes)
        self.assertEqual(len(review.comments), 1)
        self.assertEqual(review.comments[0].line_number, 3)
        self.assertEqual(review.comments[0].comment, "test_review")


class TestProgrammingPrincipleReviewer(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        principle_path = Path(__file__).parents[1] / ".coding_principles" / "single_responsibility.yaml"
        container = Container.from_config(
            AppConfig(
                principles_path=[principle_path],
                llm_model_name="gpt-3.5-turbo"
            )
        )
        self.reviewer = container.reviewers()[0]
        mock_diff_path = Path(__file__).parent / "data" / "mock_diff.txt"
        with open(mock_diff_path) as f:
            self.test_diff = f.read()

    async def test_review(self):
        reviews = await self.reviewer.review_file_diff(self.test_diff)
        self.assertGreater(len(reviews.comments), 0)

    async def test_empty_review(self):
        test_diff = """"""
        reviews = await self.reviewer.review_file_diff(test_diff)
        self.assertEqual(len(reviews.comments), 0)
