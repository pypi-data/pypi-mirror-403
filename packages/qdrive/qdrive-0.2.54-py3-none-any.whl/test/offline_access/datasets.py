'''
Test to ensure that datasets can be loaded when being offline.

1) create a dataset and get it by uuid
2) create a dataset and perform a search, make sure the datasets are found

'''
from qdrive.dataset.dataset import dataset
from qdrive.dataset.search import search_datasets

def test_create_dataset_get_by_uuid(simulated_error):
    """
    Test 1: Create a dataset and then load it by its UUID.
    """
    # Create a dataset (the offline db should handle this)
    ds = dataset.create(
        name="Test Dataset",
        description="Test Description",
        keywords=["test"],
        attributes={"key": "value"}
    )
    # Retrieve the dataset using its uuid.
    ds_loaded = dataset(str(ds.uuid))
    
    assert str(ds.uuid) == str(ds_loaded.uuid)
    assert ds_loaded.name == "Test Dataset"

def test_create_dataset_and_search(simulated_error):
    """
    Test 2: Create a dataset and perform a search to verify that it is found.
    """
    test_name = "Searchable Dataset"
    # Create the dataset.
    ds = dataset.create(
        name=test_name,
        description="Dataset for search test",
        keywords=["search"],
        attributes={"key": "value"}
    )
    
    # Perform a search with a query matching the dataset name.
    search_result = search_datasets(search_query=test_name)
    
    # Iterate over the search result; the SearchResult is an iterator.
    found = False
    try:
        for ds_item in search_result:
            if str(ds_item.uuid) == str(ds.uuid):
                found = True
                break
    except ValueError:
        # In case no results are returned.
        found = False
        
    assert found, "Created dataset was not found in search results."