from typing import List

from pydantic import BaseModel


class FileDiffComment(BaseModel):
    line_number: int
    comment: str


class FileDiffReview(BaseModel):
    comments: List[FileDiffComment]

    @property
    def approve(self) -> bool:
        return len(self.comments) == 0
