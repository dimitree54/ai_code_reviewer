from typing import List

from pydantic.v1 import BaseModel as BaseModelV1


class FilePatchComment(BaseModelV1):
    line_number: int
    comment: str


class FilePatchReview(BaseModelV1):
    comments: List[FilePatchComment]

    @property
    def approve(self) -> bool:
        return len(self.comments) == 0
