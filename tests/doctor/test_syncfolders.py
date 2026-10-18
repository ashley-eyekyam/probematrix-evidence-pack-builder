"""Sync-folder detection (WS-12, design A1). Every test passes ``home``, ``environ`` and
``platform`` explicitly, so nothing reads the real home folder."""

import json

import pytest
from epb.doctor import syncfolders


def providers(hits):
    return [hit.provider for hit in hits]


def check(path, home, *, environ=None, platform="linux"):
    return syncfolders.check(path, home=home, environ=environ or {}, platform=platform)


@pytest.fixture
def home(tmp_path):
    path = tmp_path / "home"
    path.mkdir()
    return path


def write_dropbox_info(info_path, accounts):
    info_path.parent.mkdir(parents=True, exist_ok=True)
    info_path.write_text(json.dumps(accounts), encoding="utf-8")


# --- registry -----------------------------------------------------------------------------


def test_providers_cover_the_four_services():
    names = [provider.name for provider in syncfolders.PROVIDERS]
    for name in ("Dropbox", "OneDrive", "Google Drive", "iCloud Drive"):
        assert name in names


# --- Dropbox info.json --------------------------------------------------------------------


def test_dropbox_personal_path_from_info_json(home, tmp_path):
    synced = tmp_path / "Work Files"
    case = synced / "case-a"
    case.mkdir(parents=True)
    write_dropbox_info(home / ".dropbox" / "info.json", {"personal": {"path": str(synced)}})
    hits = check(case, home)
    assert providers(hits) == ["Dropbox"]
    assert hits[0].root == str(synced.resolve())


def test_dropbox_business_path_from_info_json(home, tmp_path):
    synced = tmp_path / "Team Space"
    case = synced / "x" / "case"
    case.mkdir(parents=True)
    write_dropbox_info(
        home / ".dropbox" / "info.json",
        {"personal": {"path": str(tmp_path / "elsewhere")}, "business": {"path": str(synced)}},
    )
    assert providers(check(case, home, platform="darwin")) == ["Dropbox"]


@pytest.mark.parametrize("variable", ["APPDATA", "LOCALAPPDATA"])
def test_dropbox_info_json_on_windows(home, tmp_path, variable):
    app_data = tmp_path / variable
    synced = tmp_path / "Shared Work"
    case = synced / "case"
    case.mkdir(parents=True)
    write_dropbox_info(app_data / "Dropbox" / "info.json", {"personal": {"path": str(synced)}})
    hits = check(case, home, environ={variable: str(app_data)}, platform="win32")
    assert providers(hits) == ["Dropbox"]


@pytest.mark.parametrize(
    "content",
    ["{not json", "[]", '{"personal": "nope"}', '{"personal": {"path": 7}}', ""],
    ids=["invalid", "list", "not-a-dict", "path-not-text", "empty"],
)
def test_damaged_dropbox_info_json_means_no_root(home, tmp_path, content):
    info = home / ".dropbox" / "info.json"
    info.parent.mkdir(parents=True)
    info.write_text(content, encoding="utf-8")
    case = tmp_path / "plain" / "case"
    case.mkdir(parents=True)
    assert check(case, home) == []


def test_missing_dropbox_info_json_means_no_root(home, tmp_path):
    case = tmp_path / "plain" / "case"
    case.mkdir(parents=True)
    assert check(case, home) == []


# --- OneDrive -----------------------------------------------------------------------------


@pytest.mark.parametrize("value", ['"~/Sync Here"', "~/Sync Here", '"{home}/Sync Here"'])
def test_onedrive_linux_config_sync_dir(home, value):
    config = home / ".config" / "onedrive" / "config"
    config.parent.mkdir(parents=True)
    config.write_text(
        '# comment\nskip_file = "~*"\nsync_dir = ' + value.format(home=home) + "\n",
        encoding="utf-8",
    )
    case = home / "Sync Here" / "case"
    case.mkdir(parents=True)
    hits = check(case, home)
    assert providers(hits) == ["OneDrive"]
    assert hits[0].root == str((home / "Sync Here").resolve())


def test_onedrive_linux_config_ignored_on_other_os(home):
    config = home / ".config" / "onedrive" / "config"
    config.parent.mkdir(parents=True)
    config.write_text('sync_dir = "~/Sync Here"\n', encoding="utf-8")
    case = home / "Sync Here" / "case"
    case.mkdir(parents=True)
    assert check(case, home, platform="win32") == []


def test_onedrive_macos_cloudstorage(home):
    root = home / "Library" / "CloudStorage" / "OneDrive-Contoso"
    case = root / "case"
    case.mkdir(parents=True)
    hits = check(case, home, platform="darwin")
    assert providers(hits) == ["OneDrive"]
    assert hits[0].root == str(root.resolve())


@pytest.mark.parametrize("variable", ["OneDrive", "OneDriveConsumer", "OneDriveCommercial"])
def test_onedrive_windows_variables(home, tmp_path, variable):
    root = tmp_path / "Corporate Sync"
    case = root / "case"
    case.mkdir(parents=True)
    hits = check(case, home, environ={variable: str(root)}, platform="win32")
    assert providers(hits) == ["OneDrive"]


def test_windows_root_comparison_ignores_case(home, tmp_path):
    root = tmp_path / "Corporate Sync"
    case = tmp_path / "CORPORATE SYNC" / "case"
    case.mkdir(parents=True)
    hits = check(case, home, environ={"OneDrive": str(root)}, platform="win32")
    assert providers(hits) == ["OneDrive"]


# --- Google Drive and iCloud Drive ----------------------------------------------------------


def test_google_drive_macos_cloudstorage(home):
    case = home / "Library" / "CloudStorage" / "GoogleDrive-person@example.com" / "case"
    case.mkdir(parents=True)
    assert providers(check(case, home, platform="darwin")) == ["Google Drive"]


def test_google_drive_gvfs_mount(home, tmp_path):
    mount = tmp_path / "run" / "user" / "1000" / "gvfs" / "google-drive:host=example.com,user=p"
    case = mount / "case"
    case.mkdir(parents=True)
    assert providers(check(case, home)) == ["Google Drive"]


def test_icloud_drive_macos(home):
    case = home / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "case"
    case.mkdir(parents=True)
    hits = check(case, home, platform="darwin")
    assert providers(hits) == ["iCloud Drive"]


def test_icloud_drive_windows(home):
    case = home / "iCloudDrive" / "case"
    case.mkdir(parents=True)
    assert providers(check(case, home, platform="win32")) == ["iCloud Drive"]


# --- name heuristic -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("component", "provider"),
    [
        ("OneDrive", "OneDrive"),
        ("OneDrive - Contoso", "OneDrive"),
        ("onedrive", "OneDrive"),
        ("Dropbox", "Dropbox"),
        ("Dropbox (Team)", "Dropbox"),
        ("DROPBOX", "Dropbox"),
        ("Google Drive", "Google Drive"),
        ("GoogleDrive-x", "Google Drive"),
        ("My Drive", "Google Drive"),
        ("iCloud Drive", "iCloud Drive"),
        ("iCloudDrive", "iCloud Drive"),
        ("Mobile Documents", "iCloud Drive"),
    ],
)
def test_name_heuristic(tmp_path, home, component, provider):
    case = tmp_path / "somewhere" / component / "case"
    case.mkdir(parents=True)
    hits = check(case, home)
    assert providers(hits) == [provider]
    assert hits[0].root is None


def test_cloudstorage_alone_is_a_sync_folder(tmp_path, home):
    case = tmp_path / "Library" / "CloudStorage" / "Box-Box" / "case"
    case.mkdir(parents=True)
    hits = check(case, home)
    assert len(hits) == 1


@pytest.mark.parametrize("component", ["MyDropboxNotes", "drive-images", "OneDriveBackup2"])
def test_name_heuristic_needs_a_whole_component(tmp_path, home, component):
    case = tmp_path / component / "case"
    case.mkdir(parents=True)
    assert check(case, home) == []


def test_plain_folder_has_no_hits(tmp_path, home):
    case = tmp_path / "Documents" / "case"
    case.mkdir(parents=True)
    assert check(case, home) == []


def test_provider_reported_once(home):
    root = home / "Dropbox"
    case = root / "OneDrive" / "Dropbox (Team)" / "case"
    case.mkdir(parents=True)
    write_dropbox_info(home / ".dropbox" / "info.json", {"personal": {"path": str(root)}})
    hits = check(case, home)
    assert providers(hits) == ["Dropbox", "OneDrive"]
    assert hits[0].root == str(root.resolve())


def test_case_folder_equal_to_root(home, tmp_path):
    root = tmp_path / "Corporate Sync"
    root.mkdir()
    hits = check(root, home, environ={"OneDrive": str(root)}, platform="win32")
    assert providers(hits) == ["OneDrive"]


# --- the warning --------------------------------------------------------------------------


def test_warning_for_hit():
    item = syncfolders.warning_for(syncfolders.SyncHit("Dropbox", "/x/Dropbox", "info.json"))
    assert item["code"] == "SYNC_FOLDER"
    assert "appears to be inside Dropbox" in item["message"]
    assert ".epb/private/" in item["message"]
    assert "Dropbox" in item["hint"]


# --- doctor shows the warning inside a case folder ------------------------------------------


def _dropbox_case(home_dir, case_dir):
    write_dropbox_info(
        home_dir / ".dropbox" / "info.json", {"personal": {"path": str(case_dir.parent)}}
    )


def test_doctor_warns_inside_a_case_folder(run_epb, case_dir, home_dir):
    _dropbox_case(home_dir, case_dir)
    (case_dir / ".epb").mkdir()
    proc = run_epb(["doctor", "--json"], case_dir, in_env=False)
    envelope = json.loads(proc.stdout)
    codes = [item["code"] for item in envelope["warnings"]]
    assert "SYNC_FOLDER" in codes
    folder = envelope["data"]["folder"]
    assert folder["checked"] is True
    assert "SYNC_FOLDER" in [item["code"] for item in folder["warnings"]]


def test_doctor_checks_nothing_outside_a_case_folder(run_epb, case_dir, home_dir):
    _dropbox_case(home_dir, case_dir)
    proc = run_epb(["doctor", "--json"], case_dir, in_env=False)
    envelope = json.loads(proc.stdout)
    assert envelope["warnings"] == []
    assert envelope["data"]["folder"] == {"checked": False, "warnings": []}


def test_doctor_human_output_names_the_fix(run_epb, case_dir, home_dir):
    _dropbox_case(home_dir, case_dir)
    (case_dir / ".epb").mkdir()
    proc = run_epb(["doctor"], case_dir, in_env=False)
    assert "appears to be inside Dropbox" in proc.stderr
    assert "Move the case folder to a folder that Dropbox does not sync" in proc.stderr
