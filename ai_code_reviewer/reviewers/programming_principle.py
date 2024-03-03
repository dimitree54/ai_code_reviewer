from typing import List

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableSerializable
from pydantic import BaseModel as BaseModelV2, Field
from yid_langchain_extensions.utils import pydantic_v1_port

from ai_code_reviewer.review import FilePatchReview
from ai_code_reviewer.container import build_patch_review_chain
from ai_code_reviewer.reviewers.base import Reviewer
from ai_code_reviewer.utils import add_line_numbers


class ProgrammingPrinciple(BaseModelV2):
    name: str = Field(alias="principle_name")
    description: str = Field(alias="principle_description")
    review_required_examples: str
    review_not_required_examples: str


class ProgrammingPrincipleChecker(Reviewer):
    programming_principle: ProgrammingPrinciple
    patch_review_chain: pydantic_v1_port(RunnableSerializable[List[BaseMessage], FilePatchReview]) = Field(
        default_factory=build_patch_review_chain
    )

    async def review_file_patch(self, patch: str) -> FilePatchReview:
        enumerated_patch = add_line_numbers(patch)
        file_patch_review: FilePatchReview = await self.patch_review_chain.ainvoke(
            input={
                "enumerated_patch": enumerated_patch,
                "principle_name": self.programming_principle.name,
                "principle_description": self.programming_principle.description,
                "review_required_examples": self.programming_principle.review_required_examples,
                "review_not_required_examples": self.programming_principle.review_not_required_examples
            }
        )
        return file_patch_review
