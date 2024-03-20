import asyncio
from typing import Dict, List

from tqdm.asyncio import tqdm

from ai_code_reviewer.review import FileDiffComments
from ai_code_reviewer.reviewers.base import Reviewer


class FileDiffReview(FileDiffComments):
    author: Reviewer
    file_name: str


async def run_principle_reviewer(
        programming_principle_reviewer: Reviewer, file_name: str, file_diff: str
) -> FileDiffReview:
    try:
        file_diff_comments = await programming_principle_reviewer.review_file_diff(file_diff)
        review = FileDiffReview(
            comments=file_diff_comments.comments,
            author=programming_principle_reviewer,
            file_name=file_name
        )
        return review
    except Exception:  # noqa
        return FileDiffReview(
            comments=[],
            author=programming_principle_reviewer,
            file_name=file_name
        )


async def get_reviews(
        per_file_diff: Dict[str, str],
        reviewers: List[Reviewer],
        report_progress: bool = True
) -> List[FileDiffReview]:
    coroutines = []
    for reviewer in reviewers:
        for file_name, file_diff in per_file_diff.items():
            coroutines.append(run_principle_reviewer(reviewer, file_name, file_diff))
    if report_progress:
        per_file_reviews: List[FileDiffReview] = list(await tqdm.gather(*coroutines, desc="Review in progress"))
    else:
        per_file_reviews: List[FileDiffReview] = list(await asyncio.gather(*coroutines))
    return per_file_reviews
