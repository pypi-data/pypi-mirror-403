'''
Unit tests to simulate the offline behavior of several functions.

to test :
    - get_scopes : check if at least one result is returned (confirms that the local db works)
    - get_default_scope : check if this can be retrieved (confirms that the local db works)
    - set_default_scope : check if this can be set, just use the one returned by get_scopes
        * try to set using the scope name
        * try to set using the scope UUID
        * try to set using the scope object
'''

import uuid
import pytest
from etiket_client.local.exceptions import ScopeDoesNotExistException

from qdrive.scopes import get_scopes, set_default_scope, get_default_scope
from etiket_client.settings.user_settings import user_settings


def test_get_scopes(simulated_error):
    """
    Test get_scopes: check that at least two results are returned (needed for the tests)
    """
    scopes = get_scopes()
    assert len(scopes) >= 2
    
def test_get_default_scope(simulated_error):
    """
    Test get_default_scope: check that it correctly retrieves the default scope.
    """
    # Patch the function used by get_default_scope to always return our fake scope.
    default_scope = get_default_scope()
    assert default_scope.uuid == uuid.UUID(user_settings.current_scope)
    
def test_set_default_scope(simulated_error):
    """
    Test set_default_scope by attempting to set the default scope using:
      - the scope name,
      - the scope UUID,
      - and the scope object.
    """
    old_scope = get_default_scope()
    try:
        # Get the scopes
        scopes = get_scopes()
        assert len(scopes) >= 2
        
        # Set the default scope using the scope name
        set_default_scope(scopes[0].name)
        assert user_settings.current_scope == str(scopes[0].uuid)
        
        # Set the default scope using the scope UUID
        set_default_scope(scopes[1].uuid)
        assert user_settings.current_scope == str(scopes[1].uuid)
        
        # Set the default scope using the scope object
        set_default_scope(scopes[0])
        assert user_settings.current_scope == str(scopes[0].uuid)
        
        # Try to set the default scope using an invalid type and verify the exception.
        with pytest.raises(ScopeDoesNotExistException):
            set_default_scope("this_scope_definitely_does_not_exist")
            
        with pytest.raises(TypeError):
            set_default_scope(1234)
        
        with pytest.raises(ScopeDoesNotExistException):
            set_default_scope(uuid.uuid4())
    finally:
        # Revert back to the old scope even if an error occurs.
        set_default_scope(old_scope)