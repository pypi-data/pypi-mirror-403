import numpy as np
from pymcce.utils import swing_atoms


def test_swing_atoms_rotate_around_z_axis():
    # --- Setup ---
    # One atom at (1, 0, 0)
    atom_coords = np.array([[1.0, 0.0, 0.0]])

    # Rotate around the z-axis passing through the origin
    axis_p1 = np.array([0.0, 0.0, 0.0])
    axis_p2 = np.array([0.0, 0.0, 1.0])   # direction along z

    angle_deg = 90.0  # rotate +90 degrees

    # --- Expected result ---
    # (1,0,0) rotated 90° around z becomes (0,1,0)
    expected = np.array([[0.0, 1.0, 0.0]])

    # --- Execute ---
    new_coords = swing_atoms(axis_p1, axis_p2, atom_coords, angle_deg)

    # --- Verify ---
    assert np.allclose(new_coords, expected, atol=1e-6)


def test_swing_atoms_handles_multiple_atoms():
    # Two atoms
    atom_coords = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 2.0, 0.0],
    ])

    axis_p1 = np.array([0.0, 0.0, 0.0])
    axis_p2 = np.array([0.0, 0.0, 1.0])
    angle_deg = 180.0

    # Expected: 180° around z → (x,y) → (-x,-y)
    expected = np.array([
        [-1.0,  0.0, 0.0],
        [ 0.0, -2.0, 0.0],
    ])

    new_coords = swing_atoms(axis_p1, axis_p2, atom_coords, angle_deg)

    assert np.allclose(new_coords, expected, atol=1e-6)


def test_swing_atoms_rotate_around_random_arbitrary_axis():
    rng = np.random.RandomState(42)

    # Random points and a random arbitrary axis (p1 != p2)
    atom_coords = rng.randn(5, 3)
    axis_p1 = rng.randn(3)
    axis_p2 = axis_p1 + rng.randn(3)  # ensure different point
    angle_deg = rng.uniform(-180.0, 180.0)

    def rotate_points_around_axis(points, p1, p2, angle_deg):
        theta = np.deg2rad(angle_deg)
        k = p2 - p1
        k = k / np.linalg.norm(k)
        v = points - p1  # translate so axis passes through origin
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)
        # v_rot = v*cos + (k x v)*sin + k*(k·v)*(1-cos)
        cross_term = np.cross(k, v)
        dot_kv = v.dot(k)  # shape (n,)
        v_rot = v * cos_t + cross_term * sin_t + (dot_kv[:, None] * k) * (1.0 - cos_t)
        return v_rot + p1

    expected = rotate_points_around_axis(atom_coords, axis_p1, axis_p2, angle_deg)
    new_coords = swing_atoms(axis_p1, axis_p2, atom_coords, angle_deg)

    assert np.allclose(new_coords, expected, atol=1e-6)