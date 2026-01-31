import pytest

from qdrive.utility.qcodes_metadata import QHMetaData, validate_parameter

from qcodes.instrument.parameter import ManualParameter
from qcodes.parameters import Parameter


@pytest.fixture
def static_tags():
    return ["alpha", "beta"]


@pytest.fixture
def static_attrs():
    return {"device": "devA", "temperature": "20mK", "run": 42}


@pytest.fixture
def meta(static_tags, static_attrs):
    m = QHMetaData('qh_meta', static_tags=static_tags, static_attributes=static_attrs)
    try:
        yield m
    finally:
        # Ensure we deregister the instrument between tests (qcodes enforces unique names)
        m.close()


def test_static_tags_and_attributes(meta, static_tags, static_attrs):
    assert set(meta.tags.get()) == set(static_tags)
    assert meta.attributes.get() == static_attrs


def test_add_dynamic_tags_and_attributes(meta):
    meta.add_tags(["gamma", "beta"])  # include a duplicate to ensure it's preserved
    meta.add_attributes({"run": "42", "operator": "alice"})

    tags = meta.tags.get()
    attrs = meta.attributes.get()

    assert set(tags) == set(["alpha", "beta", "gamma", "beta"])
    assert attrs == {"device": "devA", "temperature": "20mK", "run": "42", "operator": "alice"}


def test_reset_keeps_only_static(meta, static_tags, static_attrs):
    meta.add_tags(["x", "y"]) 
    meta.add_attributes({"session": "s1"})

    # Act
    meta.reset()

    # Assert
    assert set(meta.tags.get()) == set(static_tags)
    assert meta.attributes.get() == static_attrs


def test_dynamic_attribute_overrides_static(meta):
    meta.add_attributes({"device": "devB"})
    attrs = meta.attributes.get()
    assert attrs["device"] == "devB"
    assert attrs["temperature"] == "20mK"


def test_get_idn_contains_expected_fields(meta):
    idn = meta.get_idn()
    assert idn["vendor"] == "QHarbor"
    assert idn["model"] == "QHarbor Metadata Manager"


def test_validate_parameter_accepts_numeric_float():
    p = ManualParameter("p_float", initial_value=1.23)
    assert validate_parameter(p) is p


def test_validate_parameter_accepts_numeric_int():
    p = ManualParameter("p_int", initial_value=3)
    assert validate_parameter(p) is p


def test_validate_parameter_rejects_non_parameter():
    with pytest.raises(ValueError):
        validate_parameter(123)  # type: ignore[arg-type]


def test_validate_parameter_rejects_non_numeric_value():
    p = ManualParameter("p_str", initial_value="abc")
    with pytest.raises(ValueError) as ei:
        validate_parameter(p)
    assert "expected float or int" in str(ei.value)


def test_validate_parameter_wraps_get_exception():
    def _raise():
        raise RuntimeError("boom")

    p = Parameter("bad_param", get_cmd=_raise)

    with pytest.raises(ValueError) as ei:
        validate_parameter(p)

    # The function should wrap non-ValueErrors to a ValueError with a helpful message
    assert "Could not get value from parameter: bad_param" in str(ei.value)


