from fika_logger.core.component import get_component_from_caller


def test_returns_caller_filepath():
    result = get_component_from_caller()
    # Should return the path of THIS test file
    assert "test_component.py" in result
    assert "fika_logger" not in result
