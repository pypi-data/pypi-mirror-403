import pathlib, tempfile
import pytest

from etiket_client.remote.endpoints.dataset import dataset_read_by_alt_uid
from etiket_client.remote.endpoints.models.scope import ScopeRead

from qdrive.utility.uploads import upload_folder
from qdrive.utility.copy import copy_dataset
from qdrive.dataset.dataset import dataset as QDataset


def _write_text(p: pathlib.Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

def _version_id_for(p: pathlib.Path) -> int:
    return int(p.stat().st_mtime * 1000)

def _files_by_name(remote_ds) -> dict[str, list]:
    by_name: dict[str, list] = {}
    for f in remote_ds.files:
        by_name.setdefault(f.name, []).append(f)
    return by_name

def _relative_posix(base: pathlib.Path, p: pathlib.Path) -> str:
    return p.resolve().relative_to(base.resolve()).as_posix()


@pytest.mark.parametrize("direct_upload", [False, True])
def test_copy_dataset_basic(test_scopes: tuple[ScopeRead, ScopeRead, ScopeRead], direct_upload: bool):
    scope_src, scope_dst, _ = test_scopes
    with tempfile.TemporaryDirectory() as tmpdir:
        base = pathlib.Path(tmpdir)

        # Create source files
        a_txt = base / "a.txt"
        b_json = base / "nested" / "b.json"
        _write_text(a_txt, "hello")
        _write_text(b_json, "{\"k\": 1}")

        # Create source dataset locally (not direct upload)
        ds_src = upload_folder(
            base,
            scope=scope_src.uuid,
            dataset_name="copy_basic_src",
            direct_upload=direct_upload,
        )

        # Sanity: source dataset can be reloaded
        _ = QDataset(str(ds_src.uuid), str(scope_src.uuid))

        # Perform copy to destination scope
        copy_dataset(ds_src.uuid, scope_src.uuid, scope_dst.uuid)

        # Read destination by alt_uid (source uuid used as alt_uid if not set)
        ds_dst = dataset_read_by_alt_uid(str(ds_src.uuid), scope_dst.uuid)

        files_by_name = _files_by_name(ds_dst)

        # Expect both files present with correct names
        expected_names = {
            _relative_posix(base, a_txt),
            _relative_posix(base, b_json),
        }
        assert set(files_by_name.keys()) >= expected_names

        # Version IDs should match source file mtimes
        assert any(f.version_id == _version_id_for(a_txt) for f in files_by_name[_relative_posix(base, a_txt)])
        assert any(f.version_id == _version_id_for(b_json) for f in files_by_name[_relative_posix(base, b_json)])


def test_copy_dataset_incremental(test_scopes: tuple[ScopeRead, ScopeRead, ScopeRead]):
    scope_src, scope_dst, _ = test_scopes
    with tempfile.TemporaryDirectory() as tmpdir:
        base = pathlib.Path(tmpdir)

        # Initial files
        a_txt = base / "a.txt"
        _write_text(a_txt, "v1")
        v1_a = _version_id_for(a_txt)

        ds_src = upload_folder(
            base,
            scope=scope_src.uuid,
            dataset_name="copy_incremental_src",
            direct_upload=False,
        )

        # Initial copy
        copy_dataset(ds_src.uuid, scope_src.uuid, scope_dst.uuid)

        # Modify existing file to create second version and add a new file
        _write_text(a_txt, "v2")
        v2_a = _version_id_for(a_txt)

        c_txt = base / "nested" / "c.txt"
        _write_text(c_txt, "new")
        v1_c = _version_id_for(c_txt)

        # Update local dataset metadata/files
        _ = upload_folder(
            base,
            scope=scope_src.uuid,
            dataset_name="copy_incremental_src",
            direct_upload=False,
        )

        # Run copy again to propagate changes
        copy_dataset(ds_src.uuid, scope_src.uuid, scope_dst.uuid)

        # Read destination dataset and validate versions
        ds_dst = dataset_read_by_alt_uid(str(ds_src.uuid), scope_dst.uuid)
        files_by_name = _files_by_name(ds_dst)

        name_a = _relative_posix(base, a_txt)
        versions_a = sorted({f.version_id for f in files_by_name.get(name_a, [])})
        assert versions_a == sorted({v1_a, v2_a})

        name_c = _relative_posix(base, c_txt)
        versions_c = {f.version_id for f in files_by_name.get(name_c, [])}
        assert versions_c == {v1_c}
