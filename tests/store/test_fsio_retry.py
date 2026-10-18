"""``replace_with_retry`` retries only on PermissionError (WS-06, the "retry on Windows" clause).

A Windows sharing violation is simulated on Linux by patching ``os.replace`` as fsio sees it.
``time.sleep`` is patched too, so the tests are instant and the sleeps can be counted.
"""

import pytest
from epb import fsio


class FakeReplace:
    """Raises each queued exception in turn, then really moves the file."""

    def __init__(self, real_replace, errors):
        self.real_replace = real_replace
        self.errors = list(errors)
        self.calls = 0

    def __call__(self, src, dst):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        self.real_replace(src, dst)


@pytest.fixture
def sleeps(monkeypatch):
    recorded = []
    monkeypatch.setattr(fsio.time, "sleep", recorded.append)
    return recorded


@pytest.fixture
def files(tmp_path):
    src = tmp_path / "record.json.tmp"
    dst = tmp_path / "record.json"
    src.write_text("new", encoding="utf-8")
    dst.write_text("old", encoding="utf-8")
    return src, dst


def _patch_replace(monkeypatch, errors):
    fake = FakeReplace(fsio.os.replace, errors)
    monkeypatch.setattr(fsio.os, "replace", fake)
    return fake


def test_a_brief_sharing_violation_is_retried_and_the_replace_lands(monkeypatch, sleeps, files):
    src, dst = files
    fake = _patch_replace(monkeypatch, [PermissionError("locked")] * 3)

    fsio.replace_with_retry(src, dst, attempts=10, delay_s=0.25)

    assert fake.calls == 4
    assert sleeps == [0.25, 0.25, 0.25]
    assert dst.read_text(encoding="utf-8") == "new"
    assert not src.exists()


def test_a_lock_that_never_clears_reraises_after_the_last_attempt(monkeypatch, sleeps, files):
    src, dst = files
    fake = _patch_replace(monkeypatch, [PermissionError("locked")] * 50)

    with pytest.raises(PermissionError):
        fsio.replace_with_retry(src, dst, attempts=5, delay_s=0.1)

    assert fake.calls == 5
    assert sleeps == [0.1] * 4  # no sleep after the final failure
    assert dst.read_text(encoding="utf-8") == "old"
    assert src.exists()


def test_the_default_contract_is_ten_attempts_and_nine_sleeps(monkeypatch, sleeps, files):
    src, dst = files
    fake = _patch_replace(monkeypatch, [PermissionError("locked")] * 50)

    with pytest.raises(PermissionError):
        fsio.replace_with_retry(src, dst)

    assert fake.calls == 10
    assert sleeps == [0.05] * 9


@pytest.mark.parametrize(
    "error",
    [FileNotFoundError("gone"), OSError("disk error"), IsADirectoryError("dir")],
    ids=["file-not-found", "generic-oserror", "is-a-directory"],
)
def test_any_other_os_error_is_raised_at_once_without_retry(monkeypatch, sleeps, files, error):
    src, dst = files
    fake = _patch_replace(monkeypatch, [error, PermissionError("never reached")])

    with pytest.raises(type(error)) as caught:
        fsio.replace_with_retry(src, dst)

    assert caught.value is error
    assert fake.calls == 1
    assert sleeps == []
    assert dst.read_text(encoding="utf-8") == "old"


def test_a_real_missing_source_fails_immediately(sleeps, tmp_path):
    with pytest.raises(FileNotFoundError):
        fsio.replace_with_retry(tmp_path / "absent", tmp_path / "target")
    assert sleeps == []
