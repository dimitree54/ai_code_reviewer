from typing import List

from pydantic import BaseModel, Field


class FileDiffComment(BaseModel):
    line_number: int
    comment: str = Field(description="description of the problem")
    suggestion: str = Field(description="suggested improvement")
    implementation: str = Field(description="your improvement implementation")
    citation_from_principle: str = Field(description="cite the part from the principle text")
    how_citation_violated: str = Field(description="how exactly this citation violated")
    on_the_other_hand: str = Field(
        description="Try to find flaws in you previous logic. Is the principle actually violated?")
    is_violating_principle: bool = Field(
        description="True if the problem explicitly mentioned in the principle text? "
                    "False if the problem is not explicitly described in the principle,"
                    " but just a general code improvement suggestion.")


class FileDiffReview(BaseModel):
    comments: List[FileDiffComment]

    @property
    def approve(self) -> bool:
        return len(self.comments) == 0
