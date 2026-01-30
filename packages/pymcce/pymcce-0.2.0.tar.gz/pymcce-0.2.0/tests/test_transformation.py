import numpy as np
import pytest
from scipy.spatial.transform import Rotation as R

from pymcce.utils import Axis, ArbitraryAxis, Transformation
import time


def assert_close(a, b, tol=1e-8):
    assert np.allclose(a, b, atol=tol), f"\nExpected:\n{b}\nGot:\n{a}"


def test_axis_normalization():
    a = Axis(0, 0, 10)
    assert_close(a.vector, np.array([0, 0, 1]))


def test_arbitrary_axis_normalization():
    axis = ArbitraryAxis(point=[1, 2, 3], direction=[0, 0, 10])
    assert_close(axis.point, np.array([1, 2, 3]))
    assert_close(axis.vector, np.array([0, 0, 1]))


def test_translation_only():
    T = Transformation().translate(1, 2, 3)
    pts = np.array([[0, 0, 0], [1, 1, 1]])
    result = T.apply(pts)
    expected = pts + np.array([1, 2, 3])
    assert_close(result, expected)


def test_rotation_about_origin_z_90deg():
    z_axis = Axis(0, 0, 1)
    T = Transformation().rotate(z_axis, 90)
    pts = np.array([[1, 0, 0]])
    result = T.apply(pts)
    expected = np.array([[0, 1, 0]])
    assert_close(result, expected)


def test_rotation_about_arbitrary_axis():
    # Rotate around z-axis passing through (1,0,0) by 90°
    axis = ArbitraryAxis(point=[1, 0, 0], direction=[0, 0, 1])
    T = Transformation().rotate_about_axis(axis, 90)

    pts = np.array([[2, 0, 0]])  # one unit away from axis point
    result = T.apply(pts)

    # Expect it to move to (1,1,0)
    expected = np.array([[1, 1, 0]])
    assert_close(result, expected)


def test_inverse_restores_original_points():
    z_axis = Axis(0, 0, 1)
    T = Transformation().rotate(z_axis, 45).translate(1, 2, 3)
    pts = np.random.rand(10, 3)

    transformed = T.apply(pts)
    recovered = T.inverse().apply(transformed)
    assert_close(recovered, pts)


def test_persistence_and_reset():
    T = Transformation()
    z_axis = Axis(0, 0, 1)

    # First rotation
    T.rotate(z_axis, 90)
    m1 = T.matrix.copy()

    # Second translation accumulates
    T.translate(1, 0, 0)
    assert not np.allclose(T.matrix, m1)

    # Reset clears everything
    T.reset()
    assert_close(T.matrix, np.eye(4))


def test_chaining_order_natural():
    """
    Ensure transformations apply in the same order they are called:
    rotate then translate -> rotate first, translate after
    """
    pts = np.array([[1, 0, 0]])
    z_axis = Axis(0, 0, 1)

    # Rotate 90°, then translate +1 along x
    T = Transformation().rotate(z_axis, 90).translate(1, 0, 0)
    result = T.apply(pts)
    # Rotation gives (0,1,0), then translation adds +1 to x
    expected = np.array([[1, 1, 0]])
    assert_close(result, expected)

def test_chaining_order_multiple_rotations():
    """
    Ensure multiple rotations apply in the same order they are called:
    rotate around z then around y -> z rotation first, then y rotation
    """
    pts = np.array([[1, 0, 0]])
    z_axis = Axis(0, 0, 1)
    y_axis = Axis(0, 1, 0)

    # Rotate 90° around z, then 90° around y
    T = Transformation().rotate(z_axis, 90).rotate(y_axis, 90)
    result = T.apply(pts)
    # In right-hand rule, first rotation gives (0,1,0), this makes the point on y axis
    # Second rotation around y keeps y the same, x=0, y=1, z=0
    expected = np.array([[0, 1, 0]])
    assert_close(result, expected)

def test_geom_2v_onto_2v():
    src1 = [0, 0, 0]
    src2 = [1, 0, 0]
    dst1 = [2, 3, 4]
    dst2 = [2, 3, 5]

    T = Transformation.geom_2v_onto_2v(src1, src2, dst1, dst2)
    pts = np.array([src1, src2])
    transformed_pts = T.apply(pts)
    expected = np.array([dst1, dst2])
    assert_close(transformed_pts, expected)


# Test for geom_3v_onto_3v
#-----------------------------------------------------
TOL = 1e-9  # numerical tolerance
def almost_equal(a, b, tol=TOL):
    return np.allclose(a, b, atol=tol, rtol=0)

@pytest.mark.parametrize("src_points, dst_points", [
    # --- Case 1: Identity (no change) ---
    (
        np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
        np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    ),

    # --- Case 2: Translation only ---
    (
        np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
        np.array([[2, 3, 4], [3, 3, 4], [2, 4, 4]])
    ),

    # --- Case 3: Rotation around Z-axis by 90 degrees ---
    (
        np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
        np.array([[0, 0, 0], [0, 1, 0], [-1, 0, 0]])
    ),

    # --- Case 4: Rotation and translation ---
    (
        np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
        np.array([[5, -2, 1], [5, -1, 1], [4, -2, 1]])
    ),

    # --- Case 5: Arbitrary rotated triangle in 3D space ---
    (
        np.array([[1, 2, 3], [2, 2, 3], [1, 3, 3]]),
        np.array([[4, 0, 2], [4, 1, 2], [4, 0, 3]])
    ),
])


def test_geom_3v_onto_3v(src_points, dst_points):
    src1, src2, src3 = src_points
    dst1, dst2, dst3 = dst_points

    T = Transformation.geom_3v_onto_3v(src1, src2, src3, dst1, dst2, dst3)
    transformed = T.apply(src_points)

    # Test that transformed source points match destination points
    assert almost_equal(transformed, dst_points), f"Transformation failed.\nExpected:\n{dst_points}\nGot:\n{transformed}"

    # Check that distances between points are preserved (rigid motion)
    def pairwise_distances(pts):
        return np.linalg.norm(pts[1] - pts[0]), np.linalg.norm(pts[2] - pts[0]), np.linalg.norm(pts[2] - pts[1])
    
    src_dists = pairwise_distances(src_points)
    dst_dists = pairwise_distances(transformed)
    assert almost_equal(src_dists, dst_dists), f"Distance mismatch. src: {src_dists}, dst: {dst_dists}"

    # Check that the transformation matrix is orthonormal (rotation part)
    R = T.matrix[:3, :3]
    should_be_I = R @ R.T
    assert almost_equal(should_be_I, np.eye(3)), f"Rotation matrix not orthonormal:\n{R}"

def test_invalid_input_collinear():
    """Test that collinear source points raise an error."""
    src = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
    dst = np.array([[0, 0, 0], [0, 1, 0], [0, 2, 0]])
    with pytest.raises(Exception):
        Transformation.geom_3v_onto_3v(*src, *dst)

#------------------Test geom_3v_onto_3v ends-----------------------------------