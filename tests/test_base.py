import unittest
from ai_code_reviewer.base import TestReviewer


class Review:
    def __init__(self, line_number: int, comment: str):
        self.line_number = line_number
        self.comment = comment


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.test_reviewer = TestReviewer()

    def test_reviewer(self):
        test_changes = "Some test changes"
        expected_review = Review(
            line_number=3,
            comment="test_review"
        )
        reviews = self.test_reviewer.review_file_changes(test_changes)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].line_number, expected_review.line_number)
        self.assertEqual(reviews[0].comment, expected_review.comment)


if __name__ == '__main__':
    unittest.main()
