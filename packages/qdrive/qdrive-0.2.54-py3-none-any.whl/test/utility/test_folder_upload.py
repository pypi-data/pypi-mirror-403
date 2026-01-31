'''

Set-up : create if does not exist a scope called "test_scope_upload_folder"



# test 1 : create empty folder -- check ds attributes [both for direct_upload = True and False]
--> use .QH_manifest.yaml in the folder to get uuid of the dataset.
--> check if the dataset is created using the dataset class, using the uuid.
--> run the function again, but update all the dataset_ fields in the upload_folder function.
--> check if the dataset is updated using the dataset class

# test 2 : check scope error handling [both for direct_upload = True and False]
--> create new empty folder
--> call the upload function and get the uuid
--> call again the upload function with a different scope name
--> check if an error is raised.
--> call again the upload function with a different scope name, but with the override option set to True.
--> get uuid from the .QH_manifest.yaml file
--> check if the dataset indeed uploaded in the correct scope.

# test 3 : check file upload [both for direct_upload = True and False]
--> create a folder with a hdf5 and zarr file in it.
--> call the upload function, with the option to upload zarr files set to True.
--> use the uuid to get the dataset object, and check if both files are present, and the version ids are as expected.
--> add another hdf5 file and overwrite the existing one.
--> call the upload function again:
--> check if for the file with the override, now two versions are present. and that the other file also also present
--> call the upload function again:
--> no changes in the dataset should have been made.
--> update the zarr file, now two version should be present for this one (check!)

# TODO name conflict --> if hdf5 and zarr file have the same name --> error should be raised.


# test 4: provide invalid folders and check error handling
--> provide a file instead of a folder
--> provide a non-existing folder

# 
'''

import pathlib, tempfile, datetime, json

import pytest
import yaml

from etiket_client.remote.endpoints.scope import ScopeRead

from qdrive.utility.uploads import upload_folder
from qdrive.dataset.dataset import dataset as QDataset
from etiket_client.sync.base.manifest_v2 import QH_MANIFEST_FILE


@pytest.mark.parametrize("direct_upload", [False, True])
def test_empty_folder_upload(test_scopes: tuple[ScopeRead, ScopeRead, ScopeRead], direct_upload: bool):
    scope1, _, _ = test_scopes
    with tempfile.TemporaryDirectory() as tmpdir:
        folder = pathlib.Path(tmpdir)

        name = "unit_empty_folder"
        desc = "Unit test: empty folder upload"
        tags = ["unit", "empty", "upload"]
        attrs = {"a": "1", "b": "2"}
        alt_uid = f"{name}-Direct-{direct_upload}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        collected = datetime.datetime.now(datetime.timezone.utc)

        ds = upload_folder(
            folder,
            scope=scope1.uuid,
            dataset_name=name,
            dataset_description=desc,
            dataset_tags=tags,
            dataset_attributes=attrs,
            dataset_alt_uid=alt_uid,
            dataset_collected=collected,
            direct_upload=direct_upload,
        )

        # Validate dataset metadata
        assert ds.name == name
        assert ds.description == desc
        assert set(ds.tags) >= set(tags)
        assert all(item in dict(ds.attributes).items() for item in attrs.items())

        # Validate we can re-load by UUID + scope
        ds2 = QDataset(str(ds.uuid), str(scope1.uuid))
        assert ds2.name == name

        # Manifest should have been created with dataset and scope uuids
        manifest_path = folder / QH_MANIFEST_FILE
        assert manifest_path.exists()
        manifest_raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert "dataset_uuid" in manifest_raw
        assert "scope_uuid" in manifest_raw
        assert str(ds.uuid) == str(manifest_raw["dataset_uuid"])
        assert str(scope1.uuid) == str(manifest_raw["scope_uuid"])
        
        # call upload again here --> check if the manifest file still has the same info.
        ds_again = upload_folder(
            folder,
            scope=scope1.uuid,
            dataset_name=name,
            dataset_description=desc,
            dataset_tags=tags,
            dataset_attributes=attrs,
            dataset_alt_uid=alt_uid,
            dataset_collected=collected,
            direct_upload=direct_upload,
        )
        assert ds_again.uuid == ds.uuid
        manifest_raw_again = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert str(ds_again.uuid) == str(manifest_raw_again["dataset_uuid"])
        assert str(scope1.uuid) == str(manifest_raw_again["scope_uuid"])

@pytest.mark.parametrize("direct_upload", [False, True])
def test_attribute_updates(test_scopes: tuple[ScopeRead, ScopeRead, ScopeRead], direct_upload: bool):
    scope1, _, _ = test_scopes
    with tempfile.TemporaryDirectory() as tmpdir:
        folder = pathlib.Path(tmpdir)

        name1 = "unit_attr_updates_v1"
        desc1 = "v1 description"
        tags1 = ["unit", "attr", "v1"]
        attrs1 = {"x": "1", "y": "2"}

        _ = upload_folder(
            folder,
            scope=scope1.uuid,
            dataset_name=name1,
            dataset_description=desc1,
            dataset_tags=tags1,
            dataset_attributes=attrs1,
            direct_upload=direct_upload,
        )

        name2 = "unit_attr_updates_v2"
        desc2 = "v2 description"
        tags2 = ["unit", "attr", "v2"]
        attrs2 = {"y": "3", "z": "4"}

        ds_updated = upload_folder(
            folder,
            scope=scope1.uuid,
            dataset_name=name2,
            dataset_description=desc2,
            dataset_tags=tags2,
            dataset_attributes=attrs2,
            direct_upload=direct_upload,
        )

        # Name and description should update
        assert ds_updated.name == name2
        assert ds_updated.description == desc2

        # Tags should be the union
        assert set(ds_updated.tags) >= set(tags1 + tags2)

        # Attributes should be merged, with later values taking precedence
        merged = dict(attrs1)
        merged.update(attrs2)
        assert all(item in dict(ds_updated.attributes).items() for item in merged.items())


def test_scope_override(test_scopes: tuple[ScopeRead, ScopeRead, ScopeRead]):
    scope1, scope2, _ = test_scopes
    with tempfile.TemporaryDirectory() as tmpdir:
        folder = pathlib.Path(tmpdir)

        # Initial upload in scope1
        ds_initial_scope1 = upload_folder(folder, scope=scope1.uuid, dataset_name="unit_scope_override")

        manifest_path = folder / QH_MANIFEST_FILE
        assert manifest_path.exists()
        
        manifest_raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert str(ds_initial_scope1.uuid) == str(manifest_raw["dataset_uuid"])
        assert str(scope1.uuid) == str(manifest_raw["scope_uuid"])
        
        # Second upload targeting a different scope without override should fail
        with pytest.raises(ValueError):
            upload_folder(folder, scope=scope2.uuid, dataset_name="unit_scope_override")

        # With override allowed, the manifest should be updated and upload should proceed
        ds_new_scope = upload_folder(
            folder,
            scope=scope2.uuid,
            dataset_name="unit_scope_override",
            allow_scope_override=True,
        )

        # Ensure we can read back the dataset using the new scope
        ds_reloaded = QDataset(str(ds_new_scope.uuid), str(scope2.uuid))
        assert ds_reloaded.name == "unit_scope_override"

        # Manifest should reflect the new scope UUID
        assert manifest_path.exists()
        
        manifest_raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert str(ds_new_scope.uuid) == str(manifest_raw["dataset_uuid"])
        assert str(scope2.uuid) == str(manifest_raw["scope_uuid"])

@pytest.mark.parametrize("direct_upload", [False, True])
def test_folder_upload_with_files(test_scopes: tuple[ScopeRead, ScopeRead, ScopeRead], direct_upload: bool):
    scope1, _, _ = test_scopes
    with tempfile.TemporaryDirectory() as tmpdir:
        folder = pathlib.Path(tmpdir)
        name = "unit_folder_with_files"
        
        # create a minimal HDF5/NetCDF file using xarray
        try:
            import xarray as xr
            import numpy as np
        except ImportError as e:
            pytest.skip(f"xarray/numpy not available: {e}")

        data = xr.Dataset({"v": ("x", np.arange(5))}, coords={"x": np.arange(5)})
        h5_path = folder / "data.h5"
        data.to_netcdf(h5_path, engine="h5netcdf", invalid_netcdf=True)

        # create a json file in the folder with sample content
        json_path = folder / "info.json"
        json_path.write_text(json.dumps({"hello": "world", "n": 1}), encoding="utf-8")

        # create a folder called files and add test.html as file with sample content
        subdir = folder / "files"
        subdir.mkdir(parents=True, exist_ok=True)
        html_path = subdir / "test.html"
        html_path.write_text("<html><body>test</body></html>", encoding="utf-8")

        # call the upload function
        ds = upload_folder(folder, scope=scope1.uuid, dataset_name=name, direct_upload=direct_upload)

        # check that all files are present and only a single version exists for each file
        for rel in ["data.h5", "info.json", "files/test.html"]:
            f = ds[rel]
            assert len(f.versions) == 1

        # call the upload function again (no changes)
        ds_again = upload_folder(folder, scope=scope1.uuid, dataset_name=name, direct_upload=direct_upload)

        # still single version for each
        for rel in ["data.h5", "info.json", "files/test.html"]:
            f = ds_again[rel]
            assert len(f.versions) == 1

@pytest.mark.parametrize("direct_upload", [False, True])
def test_folder_upload_with_zarr_file(test_scopes: tuple[ScopeRead, ScopeRead, ScopeRead], direct_upload: bool):
    scope1, _, _ = test_scopes
    with tempfile.TemporaryDirectory() as tmpdir:
        folder = pathlib.Path(tmpdir)

        name = "unit_folder_with_files_and_zarr"
        
        # Add a zarr file to the folder (e.g. export from xarray)
        try:
            import xarray as xr
            import numpy as np
        except ImportError as e:
            pytest.skip(f"xarray/numpy not available: {e}")

        zarr_dir = folder / "image.zarr"
        data = xr.Dataset({"v": ("x", np.arange(10))}, coords={"x": np.arange(10)})
        data.to_zarr(zarr_dir)

        # call the upload function with zarr conversion enabled
        ds = upload_folder(folder, scope=scope1.uuid, dataset_name=name, direct_upload=direct_upload, convert_zarr_to_hdf5=True)

        # check that the zarr is represented as an hdf5 file and single version exists
        f = ds.files["image.hdf5"]
        assert len(f.versions) == 1

        # call the upload function again (no changes)
        ds_again = upload_folder(folder, scope=scope1.uuid, dataset_name=name, direct_upload=direct_upload, convert_zarr_to_hdf5=True)
        f_again = ds_again.files["image.hdf5"]
        assert len(f_again.versions) == 1

        # update the zarr file (change content)
        data2 = xr.Dataset({"v": ("x", np.arange(12))}, coords={"x": np.arange(12)})
        data2.to_zarr(zarr_dir, mode="w")

        # call the upload function again
        ds_updated = upload_folder(folder, scope=scope1.uuid, dataset_name=name, direct_upload=direct_upload, convert_zarr_to_hdf5=True)
        f_updated = ds_updated.files["image.hdf5"]
        assert len(f_updated.versions) == 2
        
@pytest.mark.parametrize("direct_upload", [False, True])
def test_folder_upload_with_multiple_file_versions(test_scopes: tuple[ScopeRead, ScopeRead, ScopeRead], direct_upload: bool):
    scope1, _, _ = test_scopes
    with tempfile.TemporaryDirectory() as tmpdir:
        folder = pathlib.Path(tmpdir)

        name = "unit_folder_with_multiple_file_versions"
        
        # create a file text.html
        html_path = folder / "text.html"
        html_path.write_text("v1", encoding="utf-8")

        # call the upload function and check the file is present, and single version
        ds = upload_folder(folder, scope=scope1.uuid, dataset_name=name, direct_upload=direct_upload)
        f = ds.files["text.html"]
        assert len(f.versions) == 1

        # update the file
        html_path.write_text("v2", encoding="utf-8")

        # call the upload function and check the file has two versions
        ds2 = upload_folder(folder, scope=scope1.uuid, dataset_name=name, direct_upload=direct_upload)
        f2 = ds2.files["text.html"]
        assert len(f2.versions) == 2

        # call the upload function again and check that no changes are made to the dataset
        ds3 = upload_folder(folder, scope=scope1.uuid, dataset_name=name, direct_upload=direct_upload)
        f3 = ds3.files["text.html"]
        assert len(f3.versions) == 2

        # update the file again and check three versions
        html_path.write_text("v3", encoding="utf-8")
        ds4 = upload_folder(folder, scope=scope1.uuid, dataset_name=name, direct_upload=direct_upload)
        f4 = ds4.files["text.html"]
        assert len(f4.versions) == 3