from abc import ABC, abstractmethod

from pydantic import BaseModel as BaseModelV2

from ai_code_reviewer.review import FileDiffComments


class Reviewer(BaseModelV2, ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    async def review_file_diff(self, diff: str) -> FileDiffComments:
        pass
