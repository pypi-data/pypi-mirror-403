import pytest
from unittest.mock import MagicMock, patch
import sys
from pyspark_udtf.utils.version_check import require_pyspark_version, check_version_compatibility

def test_require_pyspark_version_function():
    # Helper to wrap the check in a function for testing
    def use_feature(min_v):
        require_pyspark_version(min_v)
        return True

    # conftest mocks pyspark version to "4.0.0"
    
    # These should pass (return True)
    assert use_feature("3.5") is True
    assert use_feature("4.0") is True
    
    # This should fail
    with pytest.raises(ImportError) as excinfo:
        use_feature("4.1")
    assert "requires PySpark version >= 4.1" in str(excinfo.value)

def test_check_version_compatibility():
    assert check_version_compatibility("3.5") is True
    assert check_version_compatibility("4.0") is True
    assert check_version_compatibility("4.1") is False
