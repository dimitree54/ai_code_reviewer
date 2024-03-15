from langchain_core.runnables import Runnable
from pydantic import BaseModel as BaseModelV2, Field

from ai_code_reviewer.review import FileDiffComments
from ai_code_reviewer.reviewers.base import Reviewer
from ai_code_reviewer.utils import add_line_numbers


class ProgrammingPrinciple(BaseModelV2):
    name: str = Field(alias="principle_name")
    description: str = Field(alias="principle_description")
    review_required_examples: str
    review_not_required_examples: str


class ProgrammingPrincipleReviewer(Reviewer):
    programming_principle: ProgrammingPrinciple
    diff_review_chain: Runnable

    @property
    def name(self) -> str:
        return self.programming_principle.name

    class Config:
        arbitrary_types_allowed = True

    async def review_file_diff(self, diff: str) -> FileDiffComments:
        if len(diff) == 0:
            return FileDiffComments(comments=[])
        enumerated_diff = add_line_numbers(diff)
        review: FileDiffComments = await self.diff_review_chain.ainvoke(
            input={
                "enumerated_diff": enumerated_diff,
                "principle_name": self.programming_principle.name,
                "principle_description": self.programming_principle.description,
                "review_required_examples": self.programming_principle.review_required_examples,
                "review_not_required_examples": self.programming_principle.review_not_required_examples
            }
        )
        return review
