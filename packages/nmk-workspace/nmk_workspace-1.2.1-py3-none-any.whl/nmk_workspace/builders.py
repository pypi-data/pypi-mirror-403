"""
Nmk workspace plugin builders.
"""

import fnmatch
import subprocess
from pathlib import Path

from nmk.model.builder import NmkTaskBuilder
from nmk.utils import run_with_logs  # type: ignore


class SubProjectsSyncBuilder(NmkTaskBuilder):
    """
    Builder for syncing sub-projects in the workspace tree.
    """

    def build(self, root: str, to_sync: list[str]):  # type: ignore
        """
        Synchronizes all sub-modules on their git remote branch (the one declared in the .gitmodules file).

        :param root: Root path of the workspace
        :param to_sync: List of sub-modules to sync
        """

        # Build root path
        root_path = Path(root)

        # Step 1: recursively update all submodules
        self.logger.info(self.task.emoji, "> recursively update all submodules")  # type: ignore
        subprocess.run(["git", "submodule", "update", "--remote", "--recursive"], cwd=root_path, check=True)

        # Step 2: checkout branches
        self.logger.info(self.task.emoji, "> checkout submodules branches")  # type: ignore
        for submodule_path in map(lambda p: root_path / p, to_sync):
            # Get branch name
            cp: subprocess.CompletedProcess[str] = run_with_logs(  # type: ignore
                ["git", "for-each-ref", "--format='%(refname:short)'", "--points-at", "HEAD", "refs/heads"], cwd=submodule_path, check=False
            )
            submodule_log_path = submodule_path.relative_to(root_path).as_posix()
            if (cp.returncode == 0) and cp.stdout:
                # Check it out
                branch_name = cp.stdout.splitlines(keepends=False)[0].strip().strip("'")
                self.logger.info(self.task.emoji, f">> {submodule_log_path}: {branch_name}")  # type: ignore
                run_with_logs(["git", "checkout", branch_name], cwd=submodule_path, check=True)
            else:
                # Skip unknown branch
                self.logger.warning(f">> {submodule_log_path}: unknown branch, skipping checkout")  # type: ignore


class SubProjectsBuilder(NmkTaskBuilder):
    """
    Builder for sub-projects in the workspace tree.

    This builder is used to iterate on workspace sub-projects and trigger nmk build for each.
    """

    def build(  # type: ignore
        self,
        root: str,
        to_build_first: list[str],
        to_build: list[str],
        to_build_after: list[str],
        excluded: list[str],
        args: list[str] | str,
        ignore_failures: bool = False,
    ):
        """
        Build specified tasks for each sub-project.

        :param root: Root path of the workspace
        :param to_build_first: List of sub-projects paths to build first
        :param to_build: List of all sub-projects paths to be built (including the ones in to_build_first and to_build_after)
        :param to_build_after: List of sub-projects paths to build after all the others
        :param excluded: List of sub-projects glob patterns to exclude from building
        :param args: List of nmk args to use for each sub-project
        :param ignore_failures: Whether to ignore failure of sub-project builds
        """

        # Prepare args list
        args_list = args if isinstance(args, list) else [a for a in args.split(" ") if a]

        # Prepare global list of sub-projects to be built
        sub_projects: list[str] = []
        sub_projects.extend([p for p in to_build_first if p in to_build])
        sub_projects.extend([p for p in to_build if p not in to_build_after])
        sub_projects.extend([p for p in to_build_after if p in to_build])

        # Iterate on sub-projects
        built_projects: set[str] = set()
        for sub_project in sub_projects:
            # Handle duplicates
            if sub_project in built_projects:
                # Already done, skip
                continue
            built_projects.add(sub_project)

            # Some log info...
            self.logger.info(self.task.emoji, ">> ----------------------------------------------------------------")  # type: ignore
            self.logger.info(self.task.emoji, f">> Building sub-project: {sub_project}")  # type: ignore
            self.logger.info(self.task.emoji, ">> ----------------------------------------------------------------")  # type: ignore

            # Handle exclusions
            if any(fnmatch.fnmatch(sub_project, pattern) for pattern in excluded):
                self.logger.info(self.task.emoji, ">> skipped (excluded)")  # type: ignore
                continue

            # Delegate build
            sub_project_path = Path(root) / sub_project
            nmk_args = ["nmk", "--log-prefix", f"{sub_project}/"] + args_list
            self.logger.debug(">> Running command: " + " ".join(nmk_args))
            cp = subprocess.run(nmk_args, cwd=sub_project_path)

            # Handle build failure
            if cp.returncode != 0:
                error_msg = f"!! Failed to build sub-project: {sub_project} !!"
                if ignore_failures:
                    self.logger.error(error_msg)
                else:
                    raise RuntimeError(error_msg)
