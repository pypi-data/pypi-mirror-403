import numpy as np
import pytest
import time
from pymcce import sas, sasa_in_context
from pymcce.utils import sasa_python
def test_single_atom():
    coords = np.array([[0.0, 0.0, 0.0]])
    radii = np.array([1.0])
    result = sas(coords, radii, probe_radius=0.0)
    # Single atom, no neighbors, should be fully exposed
    np.testing.assert_allclose(result, [1.0], rtol=1e-6)

def test_two_atoms_far_apart():
    coords = np.array([[0.0, 0.0, 0.0],
                       [10.0, 0.0, 0.0]])
    radii = np.array([1.0, 1.0])
    result = sas(coords, radii, probe_radius=0.0)
    np.testing.assert_allclose(result, [1.0, 1.0], rtol=1e-6)

def test_two_atoms_touching():
    coords = np.array([[0.0, 0.0, 0.0],
                       [2.0, 0.0, 0.0]])  # sum of radii = 2
    radii = np.array([1.1, 1.1])  # slightly larger than 1.0
    result = sas(coords, radii, probe_radius=0.0)
    # Each atom has part of its surface blocked by the other
    assert 0 < result[0] < 1
    assert 0 < result[1] < 1

def test_two_atoms_with_probe():
    coords = np.array([[0.0, 0.0, 0.0],
                       [3.0, 0.0, 0.0]])  # slightly further apart
    radii = np.array([1.0, 1.0])
    probe_radius = 1.0
    result = sas(coords, radii, probe_radius=probe_radius)
    # Each atom should be partially blocked
    assert 0 < result[0] < 1
    assert 0 < result[1] < 1


# ======================================================================================
# SASA calculation in the presence of other atoms
# ======================================================================================

def test_single_atom_no_blocking():
    """
    A single atom in empty space: SASA should be close to 4π(r+probe)^2.
    The Monte Carlo sampling introduces slight random error, so allow tolerance.
    """
    coords = np.array([[0.0, 0.0, 0.0]])
    radii  = np.array([1.5])
    other_coords = np.zeros((0, 3))
    other_radii  = np.zeros(0)
    probe = 1.4

    expected = 4.0 * np.pi * (radii[0] + probe) ** 2

    sasa = sasa_in_context(coords, radii, other_coords, other_radii, probe)

    assert pytest.approx(sasa, rel=0.05) == expected


def test_two_atoms_block_each_other():
    """
    Two atoms very close together — each blocks part of the other's SASA.
    SASA must be LESS than 2 × SASA(single_atom).
    """
    coords = np.array([
        [0.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],  # close enough for overlap
    ])
    radii = np.array([1.5, 1.5])
    other_coords = np.zeros((0, 3))
    other_radii  = np.zeros(0)
    probe = 1.4

    sasa = sasa_in_context(coords, radii, other_coords, other_radii, probe)

    sasa_single = 4.0 * np.pi * (1.5 + probe) ** 2

    assert sasa < 2 * sasa_single


def test_background_atom_blocks_target():
    """
    A target atom with a background atom close enough to block part of its surface.
    Background atoms must reduce SASA of coords.
    """
    coords = np.array([[0.0, 0.0, 0.0]])
    radii  = np.array([1.5])

    # Background atom placed close
    other_coords = np.array([[2.0, 0.0, 0.0]])
    other_radii  = np.array([1.5])

    probe = 1.4

    sasa = sasa_in_context(coords, radii, other_coords, other_radii, probe)
    full = 4.0 * np.pi * (1.5 + probe) ** 2

    assert sasa < full


def test_combined_neighbors_include_self_group_and_background():
    """
    A target atom should be blocked by BOTH another target atom AND a background atom.
    This verifies the combined KD-tree logic is working.
    """
    coords = np.array([
        [0.0, 0.0, 0.0],   # target 1
        [3.0, 0.0, 0.0],   # target 2 (close enough)
    ])
    radii  = np.array([1.5, 1.5])

    other_coords = np.array([
        [0.0, 4.0, 0.0],   # background atom (close enough to block)
    ])
    other_radii  = np.array([1.5])

    probe = 1.4

    sasa = sasa_in_context(coords, radii, other_coords, other_radii, probe)

    # If both blocking sources work, SASA should be < "two isolated atoms"
    full = 2 * 4.0 * np.pi * (1.5 + probe) ** 2

    assert sasa < full


def test_empty_coords_returns_zero():
    """
    If there are no target atoms, SASA should be 0.
    """
    coords = np.zeros((0, 3))
    radii  = np.zeros(0)
    other_coords = np.zeros((5, 3))
    other_radii  = np.ones(5)

    assert sasa_in_context(coords, radii, other_coords, other_radii, 1.4) == 0.0


def test_no_background_same_as_original_sasa():
    """
    When other_coords is empty, SASA should equal the SASA of coords only.
    """
    coords = np.array([[0, 0, 0]])
    radii  = np.array([1.5])
    probe = 1.4

    sasa1 = sasa_in_context(coords, radii, np.zeros((0,3)), np.zeros(0), probe)
    sasa2 = 4.0 * np.pi * (1.5 + probe)**2

    assert pytest.approx(sasa1, rel=0.05) == sasa2


def test_sasa_speed():
    """
    Benchmark comparing pure Python versus Numba-accelerated SASA.
    Reports speedup as printed lines in the pytest output.
    """

    # Generate random atoms for a meaningful benchmark
    np.random.seed(0)
    N = 60   # target atoms
    M = 80   # background atoms

    coords = np.random.randn(N, 3) * 5
    radii  = np.ones(N) * 1.5

    other_coords = np.random.randn(M, 3) * 5
    other_radii  = np.ones(M) * 1.5

    probe = 1.4

    # ------------------------------------------------------------
    # Warm-up: run once to trigger Numba compilation
    # ------------------------------------------------------------
    sasa_in_context(coords, radii, other_coords, other_radii, probe)

    # ------------------------------------------------------------
    # Time Numba version
    # ------------------------------------------------------------
    t1_start = time.time()
    sasa1 = sasa_in_context(coords, radii, other_coords, other_radii, probe)
    t1 = time.time() - t1_start

    # ------------------------------------------------------------
    # Time pure Python version (slow!) outside benchmark to avoid very long runs
    # ------------------------------------------------------------
    t0_start = time.time()
    sasa0 = sasa_python(coords, radii, other_coords, other_radii, probe)
    t0 = time.time() - t0_start

    speedup = t0 / t1

    print("\n")
    print(f"SASA pure Python: {t0:.4f} sec, value: {sasa0:.4f}")
    print(f"SASA Numba:       {t1:.4f} sec, value: {sasa1:.4f}")
    print(f"Speedup:          {speedup:.2f}×")

    # Just assert that Numba is substantially faster
    assert speedup > 5.0   # should usually be >20×
    assert np.isclose(sasa0, sasa1, rtol=0.05)