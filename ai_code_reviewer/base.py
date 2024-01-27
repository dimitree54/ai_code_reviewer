from abc import ABC
from typing import List

from pydantic import BaseModel


class Review(BaseModel):
    line_number: int
    comment: str


class Reviewer(BaseModel, ABC):
    def review_file_changes(self, hunk_with_line_numbers: str) -> List[Review]:
        pass


class FakeReviewer(Reviewer):
    def review_file_changes(self, file_changes: str) -> List[Review]:
        return []


class TestReviewer(Reviewer):
    def review_file_changes(self, file_changes: str) -> List[Review]:
        return [
            Review(
                line_number=3,
                comment="test_review"
            )
        ]
