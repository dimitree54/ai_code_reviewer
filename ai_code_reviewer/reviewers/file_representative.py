from typing import List

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableSerializable
from pydantic import BaseModel
from yid_langchain_extensions.utils import pydantic_v1_port

from ai_code_reviewer.review import FilePatchReview
from ai_code_reviewer.reviewers.base import Reviewer
from ai_code_reviewer.utils import add_line_numbers


class CodeFile(BaseModel):
    file_name: str
    file_content: str


class FileRepresentativeReviewer(Reviewer):
    code_file: CodeFile
    patch_review_chain: pydantic_v1_port(RunnableSerializable[List[BaseMessage], FilePatchReview])
    # todo make prompt

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
