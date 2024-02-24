from abc import ABC
from typing import List, Dict

from langchain import hub
from langchain.output_parsers import PydanticOutputParser
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from pydantic import BaseModel as BaseModelV2, Field
from pydantic.v1 import BaseModel as BaseModelV1
from yid_langchain_extensions.utils import pydantic_v1_port

from ai_code_reviewer.utils import add_line_numbers


class FilePatchComment(BaseModelV1):
    line_number: int  # enumeration starts from first hunk
    comment: str


class FilePatchReview(BaseModelV1):
    comments: List[FilePatchComment]

    @property
    def approve(self) -> bool:
        return len(self.comments) == 0


class Reviewer(BaseModelV2, ABC):
    async def review_file_patch(self, patch: str) -> FilePatchReview:
        pass


class ProgrammingPrinciple(BaseModelV2):
    name: str = Field(alias="principle_name")
    description: str = Field(alias="principle_description")
    review_required_examples: str
    review_not_required_examples: str


def build_patch_review_chain() -> RunnableSerializable[Dict, FilePatchReview]:
    llm = ChatOpenAI(
        model_name="gpt-4-0125-preview",
        temperature=0
    )
    output_parser = PydanticOutputParser(pydantic_object=FilePatchReview)

    principle_checking_template: ChatPromptTemplate = hub.pull("dimitree54/code_review_single_responsibility")
    principle_checking_template = principle_checking_template.partial(
        format_instructions=output_parser.get_format_instructions()
    )
    return principle_checking_template | llm | output_parser


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
