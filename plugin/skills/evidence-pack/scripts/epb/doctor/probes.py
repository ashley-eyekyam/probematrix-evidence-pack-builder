"""Doctor probes (stub; filled in by the GREEN commit)."""


def probe_tool(spec, *, which=None, run=None, platform=None):
    raise NotImplementedError


def core_requirements(*, platform=None):
    raise NotImplementedError


def probe_environment():
    raise NotImplementedError


def env_packages(env_python, names):
    raise NotImplementedError


def collect(case_dir, *, which=None, run=None):
    raise NotImplementedError
