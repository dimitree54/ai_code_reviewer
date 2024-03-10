import os
import subprocess
import unittest
from pathlib import Path


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.repo_path = Path(__file__).parents[1]
        self.cli_path = self.repo_path / "ai_code_reviewer" / "cli.py"
        self.env = {
            "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
            "PYTHONPATH": str(self.repo_path),
            "PATH": os.environ["PATH"]
        }

    def test_cli_default_no_diff(self):
        result = subprocess.run([
            'python', str(self.cli_path),
            '--repo_path', str(self.repo_path),
        ], capture_output=True, text=True, cwd=str(self.repo_path), env=self.env)
        self.assertIn("No diff with HEAD.", result.stderr)


class TestCLIWithFakeDiff(unittest.TestCase):
    def setUp(self):
        self.repo_path = Path(__file__).parents[1]
        self.cli_path = self.repo_path / "ai_code_reviewer" / "cli.py"

        self.env = {
            "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
            "PYTHONPATH": str(self.repo_path),
            "PATH": os.environ["PATH"]
        }

        mock_diff_path = Path(__file__).parent / "data" / "mock_diff.txt"
        with open(mock_diff_path) as f:
            test_diff = f.read()
        self.fake_repo_file_path = self.repo_path / "fake_repo_file.py"
        with open(self.fake_repo_file_path, "w") as fake_repo_file:
            fake_repo_file.write(test_diff)
        subprocess.run([
            'git', 'add', str(self.fake_repo_file_path),
        ], cwd=str(self.repo_path))

    def tearDown(self):
        os.remove(self.fake_repo_file_path)

    def test_cli(self):
        result = subprocess.run([
            'python', str(self.cli_path),
            '--repo_path', str(self.repo_path),
            '--openai_model_name', "gpt-3.5-turbo",
            '--custom_principles_path', str(self.repo_path / ".coding_principles"),
            '--file_extensions_to_review', ".py", ".md"
        ], capture_output=True, text=True, cwd=str(self.repo_path), env=self.env)
        self.assertIn("Review completed", result.stderr)
