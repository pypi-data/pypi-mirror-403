'''
Test to check if it is possible to create and read datasets when offline.

Steps:
    - Create a dataset.
    - Set a file (using a key, e.g. "test_file") with an initial value ("first version").
    - Update the same file by assigning a new value ("second version"), which should create a new version.
    - Reload the dataset and verify that:
         * The latest content is "second version".
         * There are exactly two versions recorded for the file.
'''

from qdrive.dataset.dataset import dataset

def test_create_dataset_add_file_and_update_version(simulated_error):
    """
    Test to ensure that datasets can be created and read offline:
    
    1. Create a dataset.
    2. Add a file entry ("test_file") with "first version".
    3. Update the file entry to "second version" (creating a new version).
    4. Reload the dataset and verify that the file's content is "second version" and it has 2 versions.
    """
    # Create a dataset (the offline DB should handle this)
    ds = dataset.create(
        name="Test Offline Dataset",
        description="Dataset for offline file and version test",
        keywords=["offline", "test"],
        attributes={"key": "value"}
    )
    
    ds["test_file"] = "first version"
    ds["test_file"] = "second version"
        
    # Load the dataset again
    ds_loaded = dataset(str(ds.uuid))
    
    assert ds_loaded["test_file"].json == "second version"
    assert len(ds_loaded["test_file"].versions) == 2