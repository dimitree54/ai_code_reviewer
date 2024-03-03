import os
from typing import Dict, List

import yaml
from langchain import hub
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI

from ai_code_reviewer.review import FilePatchReview
from ai_code_reviewer.reviewers.programming_principle import ProgrammingPrincipleChecker, ProgrammingPrinciple


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
