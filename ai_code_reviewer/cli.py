import argparse
import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Tuple, Set, List, Dict

import colorlog
from langchain_community.callbacks import get_openai_callback

from ai_code_reviewer.containers import Container, AppConfig
from ai_code_reviewer.review import FileDiffReview, FileDiffComment
from ai_code_reviewer.reviewers.base import Reviewer
from ai_code_reviewer.utils import get_files_diff


def get_logger() -> logging.Logger:
    logger = logging.getLogger("ai_code_reviewer")
    logger.setLevel(logging.INFO)
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s%(message)s'))
    logger.addHandler(handler)
    return logger


async def run_principle_reviewer(
        programming_principle_reviewer: Reviewer, file_name: str, file_diff: str
) -> Tuple[Reviewer, str, FileDiffReview]:
    try:
        review = await programming_principle_reviewer.review_file_diff(file_diff)
        return programming_principle_reviewer, file_name, review
    except Exception:  # noqa
        return programming_principle_reviewer, file_name, FileDiffReview(comments=[])


def format_review_comment(file_name: str, reviewer_name: str, review: FileDiffComment) -> str:
    return f"""./{file_name}:{review.line_number + 1}: {reviewer_name} warning:
what is violated: {review.citation_from_principle}
how it is violated: {review.how_citation_violated}
comment: {review.comment}
suggested fix: {review.suggestion}
suggestion implementation:
```
{review.implementation}
```

"""


def get_repo_diff(
        repo_path: Path,
        compare_with: str,
        allowed_extensions: Set[str],
) -> Dict[str, str]:
    per_file_diff = get_files_diff(repo_path, compare_with)
    per_file_diff = {
        file_name: file_diff for file_name, file_diff in per_file_diff.items()
        if os.path.splitext(file_name)[1] in allowed_extensions
    }
    return per_file_diff


def get_all_files(
        repo_path: Path,
        allowed_extensions: Set[str],
) -> Dict[str, str]:
    files_content = {}
    for item in repo_path.rglob('*'):
        if item.is_file() and item.suffix in allowed_extensions:
            with open(item, 'r', encoding='utf-8') as file:
                files_content[str(item.absolute())] = file.read()
    return files_content


async def get_reviews(
        per_file_diff: Dict[str, str],
        reviewers: List[Reviewer]
) -> Tuple[Reviewer, str, FileDiffReview]:
    coroutines = []
    for reviewer in reviewers:
        for file_name, file_diff in per_file_diff.items():
            coroutines.append(run_principle_reviewer(reviewer, file_name, file_diff))

    per_file_reviews = await asyncio.gather(*coroutines)
    return per_file_reviews  # noqa


def report_reviews(
        per_file_reviews: Tuple[Reviewer, str, FileDiffReview],
        logger: logging.Logger
):
    for reviewer, file_name, review in per_file_reviews:
        for comment in review.comments:
            logger.warning(format_review_comment(file_name, reviewer.name, comment))


def main():
    logger = get_logger()
    parser = argparse.ArgumentParser(description="Review code against programming principles.")
    parser.add_argument("--repo_path", type=str, required=False, default=".",
                        help="Path to the repository to review.")
    parser.add_argument("--compare_with", type=str, required=False, default="HEAD",
                        help="Base version to compare with. May be git hash or tag of source branch")
    parser.add_argument("--custom_principles_path", type=str, required=False, default=None,
                        help="If your programming principles stored not within repo/.coding_principles,"
                             " you can provide path to your principles here.")
    parser.add_argument("--openai_model_name", type=str, required=False, default="gpt-4-0125-preview",
                        help="Name of openai gpt model that will review you code.")
    parser.add_argument('--file_extensions_to_review', type=str, nargs='+', default=['.py'],
                        help='List of file extensions to review')
    parser.add_argument('--suppress_not_changed_lines', action='store_true',
                        help='Forbid reviewing not changed lines')
    parser.add_argument('--suppress_noqa_lines', action='store_true',
                        help='Forbid reviewing lines with noqa comment')
    parser.add_argument('--include_not_changed_files', action='store_true',
                        help='Review all files, not only changed ones.')
    args = parser.parse_args()

    more_info_link = "More information: https://github.com/dimitree54/ai_code_reviewer/blob/main/README.md"
    if "OPENAI_API_KEY" not in os.environ:
        logger.error(f"No OPENAI_API_KEY found. {more_info_link}")
        return

    repo_path = Path(args.repo_path)
    allowed_extensions = set(args.file_extensions_to_review)
    coding_principles_path = Path(args.custom_principles_path) if args.custom_principles_path \
        else repo_path / ".coding_principles"

    all_principles_path = [
        coding_principles_path / principle_path for principle_path in os.listdir(coding_principles_path)
        if os.path.splitext(principle_path)[1] == ".yaml"
    ]
    if len(all_principles_path) == 0:
        logger.error(
            f"No review principles found. You need to populate '{coding_principles_path}' dir with review principles."
            f" {more_info_link}")
        return
    container = Container.from_config(
            AppConfig(
                principles_path=all_principles_path,
                llm_model_name=args.openai_model_name
            )
        )

    files_to_review = get_all_files(repo_path, allowed_extensions) if args.include_not_changed_files \
        else get_repo_diff(repo_path, args.compare_with, allowed_extensions)

    with get_openai_callback() as cb:  # noqa
        start_time = time.time()
        all_reviews = asyncio.run(
            get_reviews(files_to_review, container.reviewers())
        )
        report_reviews(all_reviews, logger)
        time_spent = time.time() - start_time
        logger.info(f"Review completed in {round(time_spent, 2)}s and {round(cb.total_cost, 2)}$")


if __name__ == '__main__':
    main()
