from abc import ABC

from pydantic import BaseModel as BaseModelV2

from ai_code_reviewer.review import FilePatchReview


class Reviewer(BaseModelV2, ABC):
    async def review_file_patch(self, patch: str) -> FilePatchReview:
        pass
