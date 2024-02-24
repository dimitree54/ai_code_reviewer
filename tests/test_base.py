import unittest
from pathlib import Path

import yaml

from ai_code_reviewer.base import Reviewer, ProgrammingPrincipleChecker, ProgrammingPrinciple, FilePatchReview, \
    FilePatchComment
from ai_code_reviewer.utils import add_line_numbers


class TestAddLineNumbers(unittest.TestCase):
    def test_empty_string(self):
        self.assertEqual(add_line_numbers(""), "")

    def test_single_line(self):
        self.assertEqual(add_line_numbers("Hello, World!"), "0: Hello, World!\n")

    def test_multiple_lines(self):
        input_text = "Hello,\nWorld!"
        expected_output = "0: Hello,\n1: World!\n"
        self.assertEqual(add_line_numbers(input_text), expected_output)


class TestReviewer(Reviewer):
    async def review_file_patch(self, patch: str) -> FilePatchReview:
        return FilePatchReview(
            comments=[
                FilePatchComment(
                    line_number=3,
                    comment="test_review"
                )
            ]
        )


class MyTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_reviewer = TestReviewer()

    async def test_reviewer(self):
        test_changes = "Some test changes"
        patch_review = await self.test_reviewer.review_file_patch(test_changes)
        self.assertEqual(len(patch_review.comments), 1)
        self.assertEqual(patch_review.comments[0].line_number, 3)
        self.assertEqual(patch_review.comments[0].comment, "test_review")


class TestProgrammingPrincipleChecker(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        principle_path = Path(__file__).parents[1] / ".coding_principles" / "single_responsibility.yaml"
        with open(principle_path, "r") as file:
            programming_principle_dict = yaml.safe_load(file)
            programming_principle = ProgrammingPrinciple(**programming_principle_dict)
        self.reviewer = ProgrammingPrincipleChecker(
            programming_principle=programming_principle
        )

    async def test_review(self):
        test_patch = """
 @@ -10,20 +15,39 @@ class ReviewComment(BaseModel):


  class Reviewer(BaseModel, ABC):
 -    def review_file_changes(self, hunk_with_line_numbers: str) -> List[ReviewComment]:
 +        pass


 class FakeReviewer(Reviewer):
 -    def review_file_changes(self, file_changes: str) -> List[ReviewComment]:
 +        return []


 class TestReviewer(Reviewer):
 -    def review_file_changes(self, file_changes: str) -> List[ReviewComment]:
 +        return [
 +            ReviewComment(
 +                line_number=3,
 +                comment="test_review"
 +            )
 +        ]


 class ProgrammingPrinciple(BaseModel):
 +    name: str = Field(alias="principle_name")
 +    description: str = Field(alias="principle_description")
 +    review_required_examples: str
 +    review_not_required_examples: str


 class ReviewsOutputParser(StopSeqOutputParser[List[ReviewComment]]):
 +    def parse(self, text: str) -> List[ReviewComment]:
 +        pass  # todo


 class ProgrammingPrincipleChecker(Reviewer):
 -    llm: pydantic_v1_port(ChatOpenAI)
 -    programming_principle: ProgrammingPrinciple
 -    llm_output_parser: StopSeqOutputParser[List[ReviewComment]] = ReviewsOutputParser()
 -    principle_checking_template: ChatPromptTemplate = hub.pull("dimitree54/programming_principle_template")  # todo
 +        llm: pydantic_v1_port(ChatOpenAI)
 +        programming_principle: ProgrammingPrinciple
 +        llm_output_parser: StopSeqOutputParser[List[ReviewComment]] = ReviewsOutputParser()
 +        principle_checking_template: ChatPromptTemplate = hub.pull("dimitree54/programming_principle_template")  # todo

 -    async def review_file_changes(self, hunk_with_line_numbers: str) -> List[ReviewComment]:
 +        async def review_file_changes(self, hunk_with_line_numbers: str) -> List[ReviewComment]:
 +            messages = self.principle_checking_template.format_messages(
 +                code_diff=hunk_with_line_numbers,
 +                principle_name=self.programming_principle.name,
 +                principle_description=self.programming_principle.description,
 +                review_required_examples=self.programming_principle.review_required_examples,
 +                review_not_required_examples=self.programming_principle.review_not_required_examples,
 +                format_instructions=self.llm_output_parser.get_format_instructions()
 +            )
 +            llm_output: List[ReviewComment] = await self.llm.ainvoke(
 +                messages,
 +                stop=self.llm_output_parser.stop_sequences
 +            )
 +            return llm_output
        """
        reviews = await self.reviewer.review_file_patch(test_patch)
        print(reviews)


if __name__ == '__main__':
    unittest.main()
