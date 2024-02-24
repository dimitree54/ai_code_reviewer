import argparse
import asyncio
import os
from typing import Dict, Set

from git import Repo

import yaml

from ai_code_reviewer.base import ProgrammingPrincipleChecker, ProgrammingPrinciple


def get_repo_diff_per_file(repository_path: str, allowed_extensions: Set[str]) -> Dict[str, str]:
    repo = Repo(repository_path)
    diffs = {}
    changed_files = repo.git.diff('HEAD', name_only=True).split('\n')
    for file in changed_files:
        if os.path.splitext(file)[1] not in allowed_extensions:
            continue
        file_diff = repo.git.diff('HEAD', file)
        diffs[file] = file_diff
    return diffs


async def main(repo_path: str):
    principles_path = os.path.join(repo_path, ".coding_principles")
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
        per_file_diff = get_repo_diff_per_file(repo_path, allowed_extensions={".py"})
        for file_name in per_file_diff:
            review = await programming_principle_checker.review_file_patch(per_file_diff[file_name])
            print(f"review of file {file_name}:")
            print(review.comments)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Review code against programming principles.")
    parser.add_argument("--repo_path", type=str, required=True,
                        help="Path to the repository to review.")
    args = parser.parse_args()
    asyncio.run(main(args.repo_path))
