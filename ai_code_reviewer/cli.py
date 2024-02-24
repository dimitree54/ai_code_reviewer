import argparse
import asyncio
import logging
import os
from typing import Dict, Set

from git import Repo

import yaml

from ai_code_reviewer.base import ProgrammingPrincipleChecker, ProgrammingPrinciple


PRINCIPLES_DIR = ".coding_principles"


def get_repo_diff_per_file(repository_path: str, other: str, allowed_extensions: Set[str]) -> Dict[str, str]:
    repo = Repo(repository_path)
    diffs = {}
    changed_files = repo.git.diff(other, name_only=True).split('\n')
    for file in changed_files:
        if os.path.splitext(file)[1] not in allowed_extensions:
            continue
        file_diff = repo.git.diff(other, file)
        diffs[file] = file_diff
    return diffs


async def review_repo_diff(repo_path: str, compare_with: str):
    principles_path = os.path.join(repo_path, PRINCIPLES_DIR)
    if not os.path.isdir(principles_path) or len(os.listdir(principles_path)) == 0:
        logging.error(F"No review principles found. You need to populate '{PRINCIPLES_DIR}' dir with review principles")
        return
    for principle_file_name in os.listdir(principles_path):
        _, ext = os.path.splitext(principle_file_name)
        if ext != ".yaml":
            continue
        full_principle_file_path = os.path.join(principles_path, principle_file_name)
        with open(full_principle_file_path, "r") as file:
            programming_principle_dict = yaml.safe_load(file)
            programming_principle = ProgrammingPrinciple(**programming_principle_dict)
        programming_principle_checker = ProgrammingPrincipleChecker(
            programming_principle=programming_principle
        )
        per_file_diff = get_repo_diff_per_file(repo_path, compare_with, allowed_extensions={".py"})
        for file_name in per_file_diff:
            review = await programming_principle_checker.review_file_patch(per_file_diff[file_name])
            if not review.approve:
                logging.warning(f"Review of file {file_name}:\n{review.comments}")
    logging.info("Review completed")


def main():
    parser = argparse.ArgumentParser(description="Review code against programming principles.")
    parser.add_argument("--repo_path", type=str, required=False, default=".",
                        help="Path to the repository to review.")
    parser.add_argument("--compare_with", type=str, required=False, default="HEAD",
                        help="Base version to compare with. May be git hash or tag of source branch")
    args = parser.parse_args()
    asyncio.run(review_repo_diff(args.repo_path, args.compare_with))