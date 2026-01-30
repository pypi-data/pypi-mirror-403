import time
import numpy as np
import pytest
from pymcce.utils import LJ_energy, LJ_energy_pairwise, LJ_energy_pairwise_vectorized


# ============================================================
# Pure Python reference (slow but correct)
# ============================================================
def LJ_energy_python(coords, radii, epsilons, r_cut, sf_matrix):
    n = coords.shape[0]
    r_cut2 = r_cut * r_cut
    total = 0.0

    for i in range(n):
        for j in range(i + 1, n):
            dx = coords[i, 0] - coords[j, 0]
            dy = coords[i, 1] - coords[j, 1]
            dz = coords[i, 2] - coords[j, 2]
            r2 = dx*dx + dy*dy + dz*dz

            if r2 < r_cut2:
                sf = sf_matrix[i, j]
                if sf > 0.0:
                    sigma = 0.5 * (radii[i] + radii[j])
                    epsilon = np.sqrt(epsilons[i] * epsilons[j])

                    inv = (sigma * sigma) / r2
                    inv6 = inv * inv * inv
                    inv12 = inv6 * inv6

                    total += sf * 4.0 * epsilon * (inv12 - inv6)

    return total


# ============================================================
# Fixture: Small deterministic system
# ============================================================
@pytest.fixture
def small_test_system():
    np.random.seed(123)

    n = 50
    coords = np.random.rand(n, 3).astype(np.float32) * 10
    radii = (np.random.rand(n).astype(np.float32) * 2.0 + 2.0)
    eps = (np.random.rand(n).astype(np.float32) * 0.5 + 0.1)

    r_cut = 4.0

    # Screening matrix: 1.0 everywhere, with some exclusions
    sf = np.ones((n, n), dtype=np.float32)
    for i in range(n):
        sf[i, i] = 0.0
    sf[0, 1] = sf[1, 0] = 0.0
    sf[2, 5] = sf[5, 2] = 0.5

    return coords, radii, eps, r_cut, sf


# ============================================================
# Test accuracy
# ============================================================
def test_accuracy(small_test_system):
    coords, radii, eps, r_cut, sf = small_test_system

    # warm up Numba JIT compilation
    LJ_energy(coords, radii, eps, r_cut, sf)

    E_numba = LJ_energy(coords, radii, eps, r_cut, sf)
    E_python = LJ_energy_python(coords, radii, eps, r_cut, sf)

    # Float32 means some numeric drift is expected
    rel_err = abs(E_numba - E_python) / max(1.0, abs(E_python))

    assert rel_err < 1e-3, f"Relative error too high: {rel_err}"


# ============================================================
# Test speed (Numba must be >20× faster for N=5000)
# ============================================================
def test_speed():
    np.random.seed(123)

    n = 5000
    coords = np.random.rand(n, 3).astype(np.float32) * 30
    radii = (np.random.rand(n).astype(np.float32) * 2.0 + 2.0)
    eps = (np.random.rand(n).astype(np.float32) * 0.5 + 0.1)
    r_cut = 5.0
    sf = np.ones((n, n), dtype=np.float32)

    # Warm up Numba JIT
    LJ_energy(coords, radii, eps, r_cut, sf)

    # Time Numba version
    t0 = time.time()
    LJ_energy(coords, radii, eps, r_cut, sf)
    t_numba = time.time() - t0

    # Time Python version (slow; for n=5000 it's borderline)
    # For safety, run with smaller size and scale time
    m = 120  # less brutal, still enough to estimate
    coords_s = coords[:m]
    radii_s = radii[:m]
    eps_s = eps[:m]
    sf_s = sf[:m, :m]

    t0 = time.time()
    LJ_energy_python(coords_s, radii_s, eps_s, r_cut, sf_s)
    t_py_small = time.time() - t0

    # Estimate scaling: Python is O(N^2), so time ~ n^2
    scale = (n / m) ** 2
    t_python_est = t_py_small * scale

    speedup = t_python_est / t_numba

    print(f"Numba time: {t_numba:.4f} sec")
    print(f"Python estimated time: {t_python_est:.1f} sec")
    print(f"Speedup: {speedup:.1f}x")

    assert speedup > 20.0, f"Numba is too slow: speedup={speedup}x"


def test_LJ_energy_pairwise_basic():
    # Simple 1x1 atom groups
    coords1 = np.array([[0.0, 0.0, 0.0]])
    coords2 = np.array([[1.0, 0.0, 0.0]])
    radii1 = np.array([1.0])
    radii2 = np.array([1.0])
    eps1 = np.array([1.0])
    eps2 = np.array([1.0])
    sf_matrix = np.array([[1.0]])
    r_cut = 2.0

    energy = LJ_energy_pairwise(coords1, radii1, eps1, coords2, radii2, eps2, r_cut, sf_matrix)

    # Manually compute expected value
    sigma = radii1[0] + radii2[0]  # 2.0
    epsilon = np.sqrt(eps1[0] * eps2[0])  # 1.0
    r = 1.0
    inv_r2 = (sigma / r)**2
    inv_r6 = inv_r2**3
    inv_r12 = inv_r6**2
    expected = epsilon * (inv_r12 - 2*inv_r6) * sf_matrix[0, 0]

    assert np.isclose(energy, expected), f"Expected {expected}, got {energy}"

def test_LJ_energy_pairwise_cutoff():
    # Atoms beyond cutoff should not contribute
    coords1 = np.array([[0.0, 0.0, 0.0]])
    coords2 = np.array([[5.0, 0.0, 0.0]])  # beyond cutoff
    radii1 = np.array([1.0])
    radii2 = np.array([1.0])
    eps1 = np.array([1.0])
    eps2 = np.array([1.0])
    sf_matrix = np.array([[1.0]])
    r_cut = 2.0

    energy = LJ_energy_pairwise(coords1, radii1, eps1, coords2, radii2, eps2, r_cut, sf_matrix)
    assert energy == 0.0, "Energy should be zero for atoms beyond cutoff"

def test_LJ_energy_pairwise_screening():
    # Test screening factor scaling
    coords1 = np.array([[0.0, 0.0, 0.0]])
    coords2 = np.array([[1.0, 0.0, 0.0]])
    radii1 = np.array([1.0])
    radii2 = np.array([1.0])
    eps1 = np.array([1.0])
    eps2 = np.array([1.0])
    sf_matrix = np.array([[0.5]])  # scale by 0.5
    r_cut = 2.0

    energy_full = LJ_energy_pairwise(coords1, radii1, eps1, coords2, radii2, eps2, r_cut, np.array([[1.0]]))
    energy_scaled = LJ_energy_pairwise(coords1, radii1, eps1, coords2, radii2, eps2, r_cut, sf_matrix)

    assert np.isclose(energy_scaled, 0.5 * energy_full), "Energy should scale with screening factor"

@pytest.mark.parametrize("seed", [42, 123, 999])
def test_LJ_energy_pairwise_speed(seed):
    np.random.seed(seed)

    # Use moderately large groups so timings are measurable
    n1 = np.random.randint(50, 151)
    n2 = np.random.randint(50, 151)

    coords1 = np.random.uniform(0, 50, size=(n1, 3)).astype(np.float32)
    coords2 = np.random.uniform(0, 50, size=(n2, 3)).astype(np.float32)
    radii1 = np.random.uniform(0.5, 1.5, size=n1).astype(np.float32)
    radii2 = np.random.uniform(0.5, 1.5, size=n2).astype(np.float32)
    eps1 = np.random.uniform(0.5, 1.5, size=n1).astype(np.float32)
    eps2 = np.random.uniform(0.5, 1.5, size=n2).astype(np.float32)
    sf_matrix = np.random.uniform(0, 1, size=(n1, n2)).astype(np.float32)
    r_cut = float(np.random.uniform(2.0, 10.0))

    # Warm up JIT / caches
    LJ_energy_pairwise(coords1, radii1, eps1, coords2, radii2, eps2, r_cut, sf_matrix)
    LJ_energy_pairwise_vectorized(coords1, radii1, eps1, coords2, radii2, eps2, r_cut, sf_matrix)

    # Time each implementation (multiple repeats for stability)
    repeats = 5

    t0 = time.perf_counter()
    for _ in range(repeats):
        LJ_energy_pairwise(coords1, radii1, eps1, coords2, radii2, eps2, r_cut, sf_matrix)
    t_loop = (time.perf_counter() - t0) / repeats

    t0 = time.perf_counter()
    for _ in range(repeats):
        LJ_energy_pairwise_vectorized(coords1, radii1, eps1, coords2, radii2, eps2, r_cut, sf_matrix)
    t_vec = (time.perf_counter() - t0) / repeats

    speedup = t_loop / t_vec if t_vec > 0 else float("inf")

    print(
        f"seed={seed}: n1={n1} n2={n2} | loop={t_loop:.6f}s avg | vectorized={t_vec:.6f}s avg | speedup={speedup:.2f}x"
    )

    # Expect the vectorized implementation to be at least as fast as the loop
    assert speedup >= 1.0, f"Vectorized implementation is slower: speedup={speedup:.2f}x"