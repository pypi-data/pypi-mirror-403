import pathlib
import re

from workflow_server.core.type_checker.base import ConfigurationStatus, TypeCheckResult, WorkflowTypeChecker


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
        stdout, stderr, exit_code = mypy.api.run([str(dir), "--config-file", str(data_path)])
        return TypeCheckResult(
            success=exit_code == 0,
            type_errors=stdout,
            failure_message=stderr,
        )

    def _clean_type_errors(self, type_errors: str, dir: pathlib.Path) -> str:
        dir_prefix = re.escape(str(dir))
        pattern = re.compile(f"{dir_prefix}/?")
        return pattern.sub("", type_errors)
