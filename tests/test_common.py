import numpy as np
import pytest

from meshcomparison.common.alignment import initial_similarity_from_bboxes
from meshcomparison.common.distances import maybe_subsample, symmetric_mse
from meshcomparison.common.transforms import apply_transform_points


@pytest.fixture
def cloud():
    rng = np.random.default_rng(0)
    return rng.random((200, 3))


def test_symmetric_mse_zero_for_identical_clouds(cloud):
    assert symmetric_mse(cloud, cloud.copy()) == pytest.approx(0.0)


def test_maybe_subsample_limits_size(cloud):
    assert len(maybe_subsample(cloud, max_points=50)) == 50
    assert maybe_subsample(cloud, max_points=1000) is cloud


def test_bbox_similarity_aligns_scaled_shifted_cloud(cloud):
    moved = cloud * 2.0 + np.array([1.0, -2.0, 3.0])
    T = initial_similarity_from_bboxes(moved, cloud)
    back = apply_transform_points(moved, T)
    assert np.allclose(back.min(axis=0), cloud.min(axis=0), atol=1e-6)
    assert np.allclose(back.max(axis=0), cloud.max(axis=0), atol=1e-6)
