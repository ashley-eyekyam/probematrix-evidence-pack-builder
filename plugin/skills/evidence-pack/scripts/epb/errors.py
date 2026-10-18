"""Exit codes, stable error and warning codes, and the ``EpbError`` exception (PKG-05)."""

EXIT_OK = 0
EXIT_GATE = 1
EXIT_USAGE = 2
EXIT_MISSING_DEPENDENCY = 3
EXIT_ENVIRONMENT = 4

ERROR_CODES: dict[str, int] = {
    # 1: gate failure
    "VALIDATION_FAILED": EXIT_GATE,
    # 2: usage
    "USAGE": EXIT_USAGE,
    "BAD_ARGUMENT": EXIT_USAGE,
    "NOT_A_WORKSPACE": EXIT_USAGE,
    "WORKSPACE_EXISTS": EXIT_USAGE,
    "TIMEZONE_REQUIRED": EXIT_USAGE,
    # 3: missing dependency
    "ENV_NOT_SET_UP": EXIT_MISSING_DEPENDENCY,
    "CORE_PACKAGE_MISSING": EXIT_MISSING_DEPENDENCY,
    "PYTHON_TOO_OLD": EXIT_MISSING_DEPENDENCY,
    "VENV_UNAVAILABLE": EXIT_MISSING_DEPENDENCY,
    # 4: internal or environment
    "LOCK_TIMEOUT": EXIT_ENVIRONMENT,
    "WORKSPACE_TOO_NEW": EXIT_ENVIRONMENT,
    "STATE_INVALID": EXIT_ENVIRONMENT,
    "RECORD_INVALID": EXIT_ENVIRONMENT,
    "SETUP_FAILED": EXIT_ENVIRONMENT,
    "INTERNAL_ERROR": EXIT_ENVIRONMENT,
}

WARNING_CODES: frozenset[str] = frozenset(
    {
        "ALREADY_SET_UP",
        "RECOVERY_PENDING",
        "RECOVERED",
        "UPGRADE_PENDING",
        "WORKSPACE_UPGRADED",
        "SYNC_FOLDER",
        "GIT_TRACKS_PRIVATE",
        "GIT_PRIVATE_NOT_IGNORED",
        "GIT_UNAVAILABLE",
        "MIME_MISMATCH",
        "INPUT_REMOVED",
        "SIDECAR_ORPHAN",
        "LINK_IGNORED",
    }
)


class EpbError(Exception):
    """A failure with a stable code; the CLI turns it into an envelope and an exit code."""

    def __init__(self, code, message, *, hint=None, pointer=None, data=None):
        if code not in ERROR_CODES:
            raise ValueError(f"unknown error code: {code!r}")
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.pointer = pointer
        self.data = data

    @property
    def exit_code(self) -> int:
        return ERROR_CODES[self.code]

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
            "pointer": self.pointer,
        }


def warning(code, message, hint=None) -> dict:
    """Build one envelope warning entry; ``code`` must be in ``WARNING_CODES``."""
    if code not in WARNING_CODES:
        raise ValueError(f"unknown warning code: {code!r}")
    return {"code": code, "message": message, "hint": hint}
