from pathlib import Path
from typing import Dict, List, Type

import yaml
from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Factory, Singleton, Callable, Configuration
from langchain import hub
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from yid_langchain_extensions.llm.tools_llm_with_thought import build_tools_llm_with_thought
from yid_langchain_extensions.output_parser.pydantic_from_tool import PydanticOutputParser
from yid_langchain_extensions.utils import convert_to_openai_tool_v2

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


class ReasoningThought(BaseModel):
    reasoning: str = Field(description="Think step by step, what potential problems do you see and in what lines.")


def build_diff_review_chain(
        tools_llm: ChatOpenAI,
        review_class: Type[BaseModel],
        reasoning_class: Type[BaseModel],
        prompt: ChatPromptTemplate,
        reasoning_prompt: ChatPromptTemplate
) -> BaseModel:
    review_tool = convert_to_openai_tool_v2(review_class)
    llm_with_review_tool_and_reasoning = build_tools_llm_with_thought(
        tools_llm, [review_tool], reasoning_prompt, reasoning_class)
    pydantic_output_parser = PydanticOutputParser(
        pydantic_class=review_class,
        base_parser=OpenAIToolsAgentOutputParser()
    )
    return prompt | llm_with_review_tool_and_reasoning | pydantic_output_parser


class Container(DeclarativeContainer):
    @staticmethod
    def from_config(app_config: AppConfig) -> "Container":
        container = Container()
        container.config.from_dict(app_config.model_dump())
        return container

    config = Configuration()

    llm: Factory[ChatOpenAI] = Factory(
        ChatOpenAI, model_name=config.llm_model_name, temperature=config.llm_model_temperature)
    principle_checking_template: Singleton[ChatPromptTemplate] = Singleton(
        lambda: hub.pull("dimitree54/code_review_single_responsibility"),
    )
    reasoning_template: Singleton[ChatPromptTemplate] = Singleton(
        lambda: hub.pull("dimitree54/introduce_thought_tool"),
    )
    diff_review_chain: Callable[RunnableSerializable[Dict, FileDiffReview]] = Factory(
        build_diff_review_chain,
        tools_llm=llm,
        review_class=FileDiffReview,
        reasoning_class=ReasoningThought,
        prompt=principle_checking_template,
        reasoning_prompt=reasoning_template
    )
    reviewers: Singleton[List[Reviewer]] = Singleton(
        lambda principles_path, diff_review_chain: [
            load_principle_reviewer(principle_path, diff_review_chain) for principle_path in principles_path],
        principles_path=config.principles_path,
        diff_review_chain=diff_review_chain
    )
