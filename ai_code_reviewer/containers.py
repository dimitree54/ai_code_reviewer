from pathlib import Path
from typing import Dict, List

import yaml
from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Factory, Singleton, Callable, Configuration
from langchain import hub
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from ai_code_reviewer.review import FileDiffReview
from ai_code_reviewer.reviewers.base import Reviewer
from ai_code_reviewer.reviewers.programming_principle import ProgrammingPrincipleReviewer, ProgrammingPrinciple


def load_principle_reviewer(
        principle_yaml_path: Path, diff_review_chain: RunnableSerializable[Dict, FileDiffReview]
) -> ProgrammingPrincipleReviewer:
    with open(principle_yaml_path, "r") as file:
        programming_principle_dict = yaml.safe_load(file)
        programming_principle = ProgrammingPrinciple(**programming_principle_dict)
    reviewer = ProgrammingPrincipleReviewer(
        programming_principle=programming_principle,
        diff_review_chain=diff_review_chain
    )
    return reviewer


class AppConfig(BaseModel):
    principles_path: List[Path]
    llm_model_name: str = "gpt-4-0125-preview"
    llm_model_temperature: float = 0.0


class Container(DeclarativeContainer):
    @staticmethod
    def from_config(app_config: AppConfig) -> "Container":
        container = Container()
        container.config.from_dict(app_config.model_dump())
        return container

    config = Configuration()

    llm: Factory[ChatOpenAI] = Factory(
        ChatOpenAI, model_name=config.llm_model_name, temperature=config.llm_model_temperature)
    llm_review_parser: Factory[PydanticOutputParser] = Factory(PydanticOutputParser, pydantic_object=FileDiffReview)
    principle_checking_template_partial: Singleton[ChatPromptTemplate] = Singleton(
        lambda output_parser: hub.pull("dimitree54/code_review_single_responsibility").partial(
            format_instructions=output_parser.get_format_instructions()
        ),
        llm_review_parser
    )
    diff_review_chain: Callable[RunnableSerializable[Dict, FileDiffReview]] = Callable(
        lambda template, llm, parser: template | llm | parser,
        principle_checking_template_partial, llm, llm_review_parser
    )
    reviewers: Singleton[List[Reviewer]] = Singleton(
        lambda principles_path, diff_review_chain: [
            load_principle_reviewer(principle_path, diff_review_chain) for principle_path in principles_path],
        principles_path=config.principles_path,
        diff_review_chain=diff_review_chain
    )
