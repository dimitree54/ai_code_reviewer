from abc import ABC

from pydantic import BaseModel as BaseModelV2

from ai_code_reviewer.review import FileDiffReview


class Reviewer(BaseModelV2, ABC):
    async def review_file_diff(self, diff: str) -> FileDiffReview:
        pass
