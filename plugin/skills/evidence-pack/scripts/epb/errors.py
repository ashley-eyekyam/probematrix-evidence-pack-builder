"""Exit codes, stable error and warning codes, and the ``EpbError`` exception (PKG-05).

The code strings are a published contract: skills, agents and the user manual quote them, so
never rename one. This docstring is the source for the manual's troubleshooting chapter.

Exit codes
    0  OK. The command did what was asked; warnings may still be present.
    1  Gate failure. The content was checked and rejected; fix the content, not the setup.
    2  Usage. The command line was wrong or the folder is not what the command needs.
    3  Missing dependency. Python, the private environment or a package is missing.
    4  Internal or environment. The workspace or the plugin is in a state it cannot use.

Error codes
    VALIDATION_FAILED     (1) The evidence pack or a record failed validation.
    USAGE                 (2) Unknown command, unknown option or a missing argument.
    BAD_ARGUMENT          (2) An argument has a value the command cannot use.
    NOT_A_WORKSPACE       (2) The folder has no .epb workspace; run init first.
    WORKSPACE_EXISTS      (2) init was run again on a case folder with settings (title, slug,
                              prefix or timezone) that differ from the stored ones.
    TIMEZONE_REQUIRED     (2) No valid IANA timezone could be determined for the case.
    ENV_NOT_SET_UP        (3) First-time setup has not been run, or the private environment
                              is out of date for this plugin version; run doctor --setup.
    CORE_PACKAGE_MISSING  (3) A required package is missing from the private environment;
                              run doctor --setup.
    PYTHON_TOO_OLD        (3) Python is older than 3.11; install a newer Python.
    VENV_UNAVAILABLE      (3) Python cannot create a virtual environment on this computer
                              (on Debian or Ubuntu, the python3-venv package is missing).
    LOCK_TIMEOUT          (4) Another epb command held the workspace lock for too long.
    WORKSPACE_TOO_NEW     (4) The workspace was written by a newer plugin version.
    STATE_INVALID         (4) .epb/state.json or .epb/case.yaml is damaged or was edited by
                              hand; restore it from a backup instead of repairing it by
                              hand (D-19).
    RECORD_INVALID        (4) A stored workspace record is damaged or fails its schema.
    SETUP_FAILED          (4) doctor --setup could not finish building the environment.
    INTERNAL_ERROR        (4) An unexpected error or an interruption; details go to stderr.

Warning codes (never change the exit code)
    ALREADY_SET_UP           Nothing to do: the private environment was already current, or
                             init found the case folder already set up.
    RECOVERY_PENDING         An interrupted change was found and will be finished.
    RECOVERED                An interrupted change was finished before this command ran.
    UPGRADE_PENDING          The workspace will be upgraded by the next changing command.
    WORKSPACE_UPGRADED       The workspace was upgraded to this plugin version.
    SYNC_FOLDER              The case folder is inside a cloud sync folder.
    GIT_TRACKS_PRIVATE       Git is tracking files from the private .epb folders.
    GIT_PRIVATE_NOT_IGNORED  Git would pick up the private .epb folders.
    GIT_UNAVAILABLE          Git is not installed, so the git checks were skipped.
    MIME_MISMATCH            A file's content does not match its extension; content wins.
    INPUT_REMOVED            A previously scanned input file is no longer there.
    SIDECAR_ORPHAN           A sidecar file has no matching input file.
    LINK_IGNORED             A symbolic link in inputs/ was not followed.
    BAD_NAME_IGNORED         A file or folder in inputs/ whose name is not valid text was skipped.
"""

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
        "BAD_NAME_IGNORED",
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
