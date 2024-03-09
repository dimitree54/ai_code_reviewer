from typing import List

from pydantic.v1 import BaseModel as BaseModelV1


class FileDiffComment(BaseModelV1):
    line_number: int
    comment: str


class FileDiffReview(BaseModelV1):
    comments: List[FileDiffComment]

    @property
    def approve(self) -> bool:
        return len(self.comments) == 0
