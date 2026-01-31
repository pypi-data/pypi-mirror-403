from functools import cache
import logging
import pathlib
import re

from workflow_server.core.type_checker.base import ConfigurationStatus, TypeCheckResult, WorkflowTypeChecker

logger = logging.getLogger(__name__)


@cache
def _get_mypy_overrides() -> list[str]:
    import importlib.util

    if not importlib.util.find_spec("mypy"):
        return []

    from importlib.metadata import version

    from packaging.version import parse as parse_version

    flags = []
    try:
        if parse_version(version("mypy")) >= parse_version("1.19.0"):
            flags.append("--fixed-format-cache")
    except Exception:
        logger.warning("Failed to determine mypy version. Using default cache format.")

    return flags


class MypyWorkflowTypeChecker(WorkflowTypeChecker):
    def is_configured(self) -> ConfigurationStatus:
        try:
            import mypy.api  # noqa: F401
        except ImportError:
            return False, "mypy is not installed in the current environment"

        self._is_configured = True
        return True, None

    def _run(self, dir: pathlib.Path) -> TypeCheckResult:
        if not self._is_configured:
            return TypeCheckResult(
                success=False,
                failure_message="mypy is not configured",
            )

        import mypy.api

        data_path = pathlib.Path(__file__).parent / "serialization.mypy.ini"
        stdout, stderr, exit_code = mypy.api.run([str(dir), "--config-file", str(data_path), *_get_mypy_overrides()])
        return TypeCheckResult(
            success=exit_code == 0,
            type_errors=stdout,
            failure_message=stderr,
        )

    def _clean_type_errors(self, type_errors: str, dir: pathlib.Path) -> str:
        dir_prefix = re.escape(str(dir))
        pattern = re.compile(f"{dir_prefix}/?")
        return pattern.sub("", type_errors)
