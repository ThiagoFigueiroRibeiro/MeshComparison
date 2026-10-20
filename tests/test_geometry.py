import numpy as np
import pytest

from meshcomparison.geometry.metrics import compute_metrics


@pytest.fixture
def cloud():
    rng = np.random.default_rng(0)
    return rng.random((200, 3))


def test_identical_clouds_have_zero_error(cloud):
    m = compute_metrics(cloud, cloud.copy())
    assert m["chamfer_mean"] == pytest.approx(0.0)
    assert m["hausdorff"] == pytest.approx(0.0)
    assert m["rmse"] == pytest.approx(0.0)


def test_single_point_offset():
    a = np.array([[0.0, 0.0, 0.0]])
    b = np.array([[3.0, 4.0, 0.0]])
    m = compute_metrics(a, b)
    assert m["chamfer_mean"] == pytest.approx(5.0)
    assert m["hausdorff"] == pytest.approx(5.0)
    assert m["rmse"] == pytest.approx(5.0)
