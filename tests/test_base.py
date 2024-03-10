import os
import subprocess
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
                    comment="test_review"
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


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.repo_path = Path(__file__).parents[1]
        self.cli_path = self.repo_path / "ai_code_reviewer" / "cli.py"

    def test_cli_default_no_diff(self):
        result = subprocess.run([
            'python', str(self.cli_path),
            '--repo_path', str(self.repo_path),
        ], capture_output=True, text=True)
        self.assertIn("No diff with HEAD.", result.stderr)

    @staticmethod
    def prepare_fake_file(fake_file_path: Path):
        mock_diff_path = Path(__file__).parent / "data" / "mock_diff.txt"
        with open(mock_diff_path) as f:
            test_diff = f.read()
        with open(fake_file_path, "w") as fake_repo_file:
            fake_repo_file.write(test_diff)
        subprocess.run([
            'git', 'add', str(fake_file_path),
        ], capture_output=True, text=True)

    @staticmethod
    def cleanup_fake_file(fake_file_path: Path):
        os.remove(fake_file_path)

    def test_cli(self):
        fake_repo_file_path = self.repo_path / "fake_repo_file.py"
        self.prepare_fake_file(fake_repo_file_path)
        result = subprocess.run([
            'python', str(self.cli_path),
            '--repo_path', str(self.repo_path),
            '--openai_model_name', "gpt-3.5-turbo",
            '--custom_principles_path', str(self.repo_path / ".coding_principles"),
            '--file_extensions_to_review', ".py", ".md"
        ], capture_output=True, text=True)
        self.cleanup_fake_file(fake_repo_file_path)
        self.assertIn("Review completed", result.stderr)
