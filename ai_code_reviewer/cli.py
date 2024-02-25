import argparse
import asyncio
import logging
import os
import time
from typing import Tuple, Set

import colorlog
from langchain_community.callbacks import get_openai_callback

from ai_code_reviewer.base import ProgrammingPrincipleChecker, FilePatchReview, load_principle_checkers
from ai_code_reviewer.utils import get_files_diff


def get_logger() -> logging.Logger:
    logger = logging.getLogger("ai_code_reviewer")
    logger.setLevel(logging.INFO)
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s%(message)s'))
    logger.addHandler(handler)
    return logger


async def run_principle_checker(
        programming_principle_checker: ProgrammingPrincipleChecker, file_name: str, file_diff: str
) -> Tuple[ProgrammingPrincipleChecker, str, FilePatchReview]:
    review = await programming_principle_checker.review_file_patch(file_diff)
    return programming_principle_checker, file_name, review


async def review_repo_diff(
        repo_path: str,
        principles_dir_name: str,
        allowed_extensions: Set[str],
        compare_with: str,
        logger: logging.Logger
):
    principles_path = os.path.join(repo_path, principles_dir_name)
    if not os.path.isdir(principles_path) or len(os.listdir(principles_path)) == 0:
        logger.error(
            F"No review principles found. You need to populate '{principles_dir_name}' dir with review principles. "
            F"More information: https://github.com/dimitree54/ai_code_reviewer/blob/main/README.md")
        return
    all_reviewers = load_principle_checkers(principles_path)

    per_file_diff = get_files_diff(repo_path, compare_with)
    per_file_diff = {
        file_name: file_diff for file_name, file_diff in per_file_diff.items()
        if os.path.splitext(file_name)[1] in allowed_extensions
    }

    coroutines = []
    for reviewer in all_reviewers:
        for file_name, file_diff in per_file_diff.items():
            coroutines.append(run_principle_checker(reviewer, file_name, file_diff))

    per_file_reviews = await asyncio.gather(*coroutines)
    for reviewer, file_name, review in per_file_reviews:
        for comment in review.comments:
            logger.warning(
                f"./{file_name}:{comment.line_number + 1}: "
                f"{reviewer.programming_principle.name} warning: "
                f"{comment.comment}"
            )


def main():
    logger = get_logger()
    parser = argparse.ArgumentParser(description="Review code against programming principles.")
    parser.add_argument("--repo_path", type=str, required=False, default=".",
                        help="Path to the repository to review.")
    parser.add_argument("--compare_with", type=str, required=False, default="HEAD",
                        help="Base version to compare with. May be git hash or tag of source branch")
    args = parser.parse_args()

    principles_dir_name = ".coding_principles"
    allowed_extensions = {".py"}

    with get_openai_callback() as cb:  # noqa
        start_time = time.time()
        asyncio.run(review_repo_diff(
            args.repo_path, principles_dir_name, allowed_extensions, args.compare_with, logger
        ))
        time_spent = time.time() - start_time
        logger.info(f"Review completed in {round(time_spent, 2)}s and {round(cb.total_cost, 2)}$")
