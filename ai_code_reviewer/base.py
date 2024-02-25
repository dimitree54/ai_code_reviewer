import os
from abc import ABC
from typing import List, Dict

import yaml
from langchain import hub
from langchain.output_parsers import PydanticOutputParser
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel as BaseModelV2, Field
from pydantic.v1 import BaseModel as BaseModelV1
from yid_langchain_extensions.utils import pydantic_v1_port

from ai_code_reviewer.utils import add_line_numbers


class FilePatchComment(BaseModelV1):
    line_number: int
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


def load_principle_checkers(principles_path: str) -> List[ProgrammingPrincipleChecker]:
    all_principles = []
    for principle_file_name in os.listdir(principles_path):
        if os.path.splitext(principle_file_name)[1] != ".yaml":
            continue
        full_principle_file_path = os.path.join(principles_path, principle_file_name)
        with open(full_principle_file_path, "r") as file:
            programming_principle_dict = yaml.safe_load(file)
            programming_principle = ProgrammingPrinciple(**programming_principle_dict)
        programming_principle_checker = ProgrammingPrincipleChecker(
            programming_principle=programming_principle
        )
        all_principles.append(programming_principle_checker)
    return all_principles
