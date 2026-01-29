"""
Nmk workspace plugin config item resolvers.
"""

import re
from pathlib import Path

from nmk.logs import NmkLogger
from nmk.model.resolver import NmkListConfigResolver
from nmk.utils import run_with_logs


class SubProjectsResolver(NmkListConfigResolver):
    """
    Resolver usable find sub-projects in the workspace tree.

    Default behavior is to look sub-projects by iterating through git submodules.
    (other behaviors may be implemented if needed later).
    """

    def get_value(self, name: str, root: str, only_nmk_projects: bool = True) -> list[str]:  # type: ignore
        """
        Resolver for sub-projects list.

        :param root: root path of the workspace
        :param only_nmk_projects: if True (default), only return sub-projects having a default nmk project file (nmk.yml)
        :return: list of sub-projects paths relative to the workspace root
        """

        # Ask git for submodules paths
        root_path = Path(root)
        cp = run_with_logs(["git", "submodule", "foreach", "--recursive", "echo xxx"], cwd=root_path)
        nmk_models: list[str] = []
        SUB_MODULE_PATTERN = re.compile(r"^.+ \'(.*)\'$")
        for candidate in map(
            lambda x: x.group(1) if x is not None else None,
            filter(lambda x: x is not None, map(lambda x: SUB_MODULE_PATTERN.match(x.strip()), cp.stdout.splitlines(keepends=False))),
        ):
            # Only keep ones with a default nmk model file
            assert candidate is not None  # for type hinting
            candidate_path = Path(candidate)
            if candidate_path.is_absolute() or not (root_path / candidate_path).exists():  # pragma: no cover
                NmkLogger.debug(f"Sub-project path {candidate_path} is not valid, skipping it.")
                continue
            sub_module_path = candidate_path.as_posix()
            if (not only_nmk_projects) or (root_path / candidate_path / "nmk.yml").is_file():
                nmk_models.append(sub_module_path)
            else:
                NmkLogger.debug(f"Sub-project {sub_module_path} does not have a default nmk model file, skipping it.")
        return nmk_models
