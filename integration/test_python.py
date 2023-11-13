"""Python interface integration tests for the equity extension."""

import pytest
from openbb_core.app.model.obbject import OBBject

# pylint: disable=too-many-lines,redefined-outer-name


# pylint: disable=import-outside-toplevel,inconsistent-return-statements
@pytest.fixture(scope="session")
def obb(pytestconfig):
    """Fixture to setup obb."""
    if pytestconfig.getoption("markexpr") != "not integration":
        import openbb

        return openbb.obb


@pytest.mark.parametrize(
    "params",
    [
        ({"symbol": "RY", "provider": "tmx"}),
        ({"symbol": "RY:US", "provider": "tmx"}),
    ],
)
@pytest.mark.integration
def test_equity_profile(params, obb):
    result = obb.equity.profile(**params)
    assert result
    assert isinstance(result, OBBject)
    assert len(result.results) > 0
