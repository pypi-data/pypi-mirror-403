"""
Utility functions for PyMCCE.

This module contains helper functions and utilities that support
the main functionality of the package.

Functions are generic by the nature.

Author: Junjun Mao
Organization: City College of New York
"""

import numpy as np
from scipy.spatial import cKDTree
from .constants import SPHERE_POINTS, N_POINTS, BOND_DISTANCE_H
from scipy.spatial.transform import Rotation as R
from numba import njit


def sas(atom_coords, atom_radii, probe_radius=1.4, sphere_points=SPHERE_POINTS):
    """Calculate percentage solvent accessible surface area (SAS) for a set of atoms."""
    N = len(atom_coords)
    tree = cKDTree(atom_coords)
    sas = np.zeros(N)
    max_radius = atom_radii.max()
    probe_radii = atom_radii + probe_radius
    neighbor_radii_sq = (atom_radii + probe_radius) ** 2

    for i in range(N):
        r = probe_radii[i]
        pts = atom_coords[i] + r * sphere_points
        neighbors = tree.query_ball_point(atom_coords[i], r + max_radius)
        neighbors = [j for j in neighbors if j != i]
        if not neighbors:
            sas[i] = 1.0
            continue
        neighbor_coords = atom_coords[neighbors]
        neighbor_radii_sq_sel = neighbor_radii_sq[neighbors]
        d2 = np.sum((pts[:, None, :] - neighbor_coords[None, :, :]) ** 2, axis=2)
        mask = np.all(d2 > neighbor_radii_sq_sel, axis=1)
        sas[i] = mask.sum() / N_POINTS

    return sas


# ==============================================================================================
# SASA calculation in the presence of other atoms
# ---------------------------------------------------------
# 1. Python-side neighbor search (combined atoms)
# ---------------------------------------------------------
def precompute_neighbors(coords, radii, other_coords, other_radii, probe_radius):
    """
    Build neighbor lists in Compressed Sparse Row (CSR) format for a set of target atoms,
    considering both target and background atoms as possible neighbors.

    Parameters
    ----------
    coords : np.ndarray, shape (n, 3)
        Cartesian coordinates of the target atoms.
    radii : np.ndarray, shape (n,)
        Atomic radii for the target atoms.
    other_coords : np.ndarray, shape (m, 3)
        Cartesian coordinates of the background (other) atoms.
    other_radii : np.ndarray, shape (m,)
        Atomic radii for the background atoms.
    probe_radius : float
        Radius of the probe sphere (e.g., water molecule) to be added to each atom's radius.

    Returns
    -------
    all_coords : np.ndarray, shape (n + m, 3)
        Combined coordinates of target and background atoms.
    all_radii : np.ndarray, shape (n + m,)
        Combined radii of target and background atoms.
    indptr : np.ndarray, shape (n + 1,)
        Index pointer array for CSR format. For atom i, neighbors are in indices[indptr[i]:indptr[i+1]].
    indices : np.ndarray, shape (total_neighbors,)
        Flattened array of neighbor indices (referring to all_coords/all_radii).

    Notes
    -----
    - "CSR format" here means that for each target atom i (0 <= i < n), its neighbors are stored
      in indices[indptr[i]:indptr[i+1]]. This is analogous to the CSR format used in sparse matrices.
    - The neighbor search includes both target and background atoms, but each atom is excluded from its own neighbor list.
    - Assumes that input arrays are valid and have matching shapes as described above.
    """
    n = coords.shape[0]

    # Combined arrays for neighbor search
    all_coords = np.vstack((coords, other_coords))        # shape (n+m, 3)
    all_radii  = np.concatenate((radii, other_radii))     # shape (n+m,)

    # Precompute extended radii for neighbor filtering
    probe_radii = radii + probe_radius
    all_ext_radii = all_radii + probe_radius
    max_all_radius = all_ext_radii.max()

    tree = cKDTree(all_coords)

    # Build neighbor lists for target atoms only
    lists = []
    for i in range(n):
        r = probe_radii[i]
        neigh = tree.query_ball_point(all_coords[i], r + max_all_radius)
        # Remove the atom itself (index = i)
        neigh = [j for j in neigh if j != i]
        lists.append(neigh)

    # Convert lists → CSR
    lengths = [len(lst) for lst in lists]
    indptr = np.zeros(n + 1, dtype=np.int64)
    indptr[1:] = np.cumsum(lengths)

    indices = np.zeros(indptr[-1], dtype=np.int64)
    p = 0
    for lst in lists:
        indices[p:p+len(lst)] = lst
        p += len(lst)

    return all_coords, all_radii, indptr, indices


# ---------------------------------------------------------
# 2. Numba kernel (uses combined coords)
# ---------------------------------------------------------
@njit
def sasa_kernel(coords, radii,
                all_coords, all_radii,
                probe_radius, sphere_points,
                indptr, indices):
    n = coords.shape[0]
    P = sphere_points.shape[0]

    sasa_total = 0.0

    probe_radii = radii + probe_radius
    all_ext_radii_sq = (all_radii + probe_radius)**2

    for i in range(n):  # Only compute SASA for target atoms
        r = probe_radii[i]
        center = coords[i]

        # Sphere sample points
        pts = center + r * sphere_points
        exposed = 0

        start = indptr[i]
        end   = indptr[i+1]

        # If no neighbors, all points exposed
        if start == end:
            sasa_total += 4.0 * np.pi * (r*r)
            continue

        # Check blockage by ANY atom (target or other)
        for p in range(P):
            px, py, pz = pts[p]
            is_exposed = True

            for k in range(start, end):
                j = indices[k]
                dx = px - all_coords[j, 0]
                dy = py - all_coords[j, 1]
                dz = pz - all_coords[j, 2]
                d2 = dx*dx + dy*dy + dz*dz

                if d2 <= all_ext_radii_sq[j]:
                    is_exposed = False
                    break

            if is_exposed:
                exposed += 1

        # Convert fraction → area
        frac = exposed / P
        sasa_total += frac * 4.0 * np.pi * (r*r)

    return sasa_total


# ---------------------------------------------------------
# 3. Main function
# ---------------------------------------------------------
def sasa_in_context(coords, radii, other_coords, other_radii, probe_radius=1.4):
    """
    Compute the total solvent accessible surface area (SASA) for a set of target atoms,
    accounting for occlusion by both the target atoms themselves and a set of background atoms.

    Parameters
    ----------
    coords : np.ndarray, shape (N, 3)
        Cartesian coordinates of the target atoms.
    radii : np.ndarray, shape (N,)
        Atomic radii for the target atoms.
    other_coords : np.ndarray, shape (M, 3)
        Cartesian coordinates of the background atoms (e.g., from other molecules or residues).
    other_radii : np.ndarray, shape (M,)
        Atomic radii for the background atoms.
    probe_radius : float, optional
        Radius of the solvent probe (in the same units as coords/radii), default is 1.4.

    Returns
    -------
    sasa : float
        Total solvent accessible surface area (SASA) for the target atoms, in square units
        corresponding to the units of the input coordinates (e.g., Å² if input is in Ångströms).

    Examples
    --------
    >>> import numpy as np
    >>> coords = np.array([[0, 0, 0], [2, 0, 0]])
    >>> radii = np.array([1.5, 1.5])
    >>> other_coords = np.array([[5, 0, 0]])
    >>> other_radii = np.array([1.5])
    >>> sasa = sasa_in_context(coords, radii, other_coords, other_radii, probe_radius=1.4)
    >>> print(f"Total SASA: {sasa:.2f}")
    """
    # KDTree + neighbor lists using combined atoms
    all_coords, all_radii, indptr, indices = precompute_neighbors(
        coords, radii, other_coords, other_radii, probe_radius
    )

    # Numba SASA kernel
    sasa = sasa_kernel(
        coords, radii,
        all_coords, all_radii,
        probe_radius,
        SPHERE_POINTS,
        indptr, indices
    )

    return sasa

#--------------------------------------------------------------------------------
def sasa_python(coords, radii, other_coords, other_radii, probe=1.4):
    """
    Reference implementation for Solvent Accessible Surface Area (SASA) calculation.

    This function computes the total SASA for a set of atoms (`coords`, `radii`) in the
    presence of other atoms (`other_coords`, `other_radii`) using a pure Python approach.
    No spatial acceleration (e.g., KD-tree) or Numba is used.

    Parameters
    ----------
    coords : np.ndarray, shape (n, 3)
        Cartesian coordinates of the target atoms.
    radii : np.ndarray, shape (n,)
        Atomic radii for the target atoms.
    other_coords : np.ndarray, shape (m, 3)
        Cartesian coordinates of the background atoms.
    other_radii : np.ndarray, shape (m,)
        Atomic radii for the background atoms.
    probe : float, optional
        Probe radius (default: 1.4 Å).

    Returns
    -------
    sasa_total : float
        Total solvent accessible surface area (SASA) for the target atoms, in Å².

    Notes
    -----
    This is a reference implementation with O(n*m*P) complexity, where n is the number
    of target atoms, m is the number of background atoms, and P is the number of sphere
    sampling points. It is extremely slow and not intended for production use.
    Use only for correctness or speed comparisons.
    """
    P = SPHERE_POINTS.shape[0]
    n = coords.shape[0]

    all_coords = np.vstack((coords, other_coords))
    all_radii  = np.concatenate((radii, other_radii))
    all_ext_radii_sq = (all_radii + probe)**2

    R = radii + probe

    sasa_total = 0.0

    for i in range(n):
        cx, cy, cz = coords[i]
        r = R[i]

        exposed = 0
        for p in range(P):
            px, py, pz = cx + r*SPHERE_POINTS[p,0], cy + r*SPHERE_POINTS[p,1], cz + r*SPHERE_POINTS[p,2]

            blocked = False
            for j in range(all_coords.shape[0]):
                if j == i:
                    continue

                dx = px - all_coords[j,0]
                dy = py - all_coords[j,1]
                dz = pz - all_coords[j,2]
                d2 = dx*dx + dy*dy + dz*dz

                if d2 <= all_ext_radii_sq[j]:
                    blocked = True
                    break

            if not blocked:
                exposed += 1

        frac = exposed / P
        sasa_total += frac * 4.0 * np.pi * (r*r)

    return sasa_total
#=============================================================================


# ==============================================================================================
# Geometric transformation utilities
# ----------------------------------------------------------------------------------------------
# This section provides small, self-contained classes for working with 3D axes and an
# accumulation-style 3D Transformation class. The Transformation stores a 4x4 homogeneous
# matrix and supports composable translations and rotations (about the origin or an
# arbitrary axis). All operations return self to allow fluent chaining.
#
# Coordinate system: right-handed, +x to the right, +y up, +z out of the screen.
# ==============================================================================================
class Axis:
    """Axis through the origin defined by a direction vector.

    Parameters
    ----------
    x, y, z : float
        Components of the axis direction. The vector is normalized internally.

    Raises
    ------
    ValueError
        If the provided direction is the zero vector.
    """

    def __init__(self, x: float, y: float, z: float):
        v = np.array([x, y, z], dtype=float)
        n = np.linalg.norm(v)
        if n == 0:
            raise ValueError("Axis direction cannot be the zero vector.")
        self.vector = v / n

    def __repr__(self) -> str:
        vx, vy, vz = self.vector
        return f"Axis({vx:.3f}, {vy:.3f}, {vz:.3f})"


class ArbitraryAxis:
    """Axis defined by a point and a direction (i.e., a line in 3D).

    Parameters
    ----------
    point : array_like, shape (3,)
        A point on the axis.
    direction : array_like, shape (3,)
        Direction vector for the axis (normalized internally).

    Raises
    ------
    ValueError
        If inputs are not 3-element vectors or the direction is the zero vector.
    """

    def __init__(self, point, direction):
        point = np.asarray(point, dtype=float)
        direction = np.asarray(direction, dtype=float)
        if point.shape != (3,) or direction.shape != (3,):
            raise ValueError("Both point and direction must be 3-element vectors.")
        n = np.linalg.norm(direction)
        if n == 0:
            raise ValueError("Direction vector cannot be the zero vector.")
        self.point = point
        self.vector = direction / n

    def __repr__(self) -> str:
        p, v = self.point, self.vector
        return (f"ArbitraryAxis(point=({p[0]:.3f}, {p[1]:.3f}, {p[2]:.3f}), "
                f"dir=({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f}))")


class Transformation:
    """Accumulative 3D transformation using a 4x4 homogeneous matrix.

    The matrix is initialized to the identity. Methods modify the internal matrix and
    return self to allow method chaining, e.g.:
        T = Transformation().translate(1,0,0).rotate(Axis(0,0,1), 90)

    Notes
    -----
    - translate(dx, dy, dz) pre-multiplies the existing matrix by the translation
      (so the new operation is applied before previously accumulated ones).
    - rotate(axis, angle_deg) rotates about an axis through the origin.
    - rotate_about_axis(axis, angle_deg) rotates about an axis defined by a point
      and direction (ArbitraryAxis).
    """

    def __init__(self):
        self.matrix = np.eye(4)

    # ------------------------
    # Transformation operations
    # ------------------------

    def translate(self, dx: float, dy: float, dz: float):
        """Prepend a translation by (dx, dy, dz) to the transformation."""
        T = np.eye(4)
        T[:3, 3] = [dx, dy, dz]
        # Pre-multiply so the translation is applied before the existing transform.
        self.matrix = T @ self.matrix
        return self

    def rotate(self, axis: Axis, angle_deg: float):
        """Prepend a rotation about an axis through the origin.

        Parameters
        ----------
        axis : Axis
            Axis object whose `vector` is the rotation axis (normalized).
        angle_deg : float
            Rotation angle in degrees (right-hand rule).
        """
        rot = R.from_rotvec(np.deg2rad(angle_deg) * axis.vector)
        Rm = np.eye(4)
        Rm[:3, :3] = rot.as_matrix()
        self.matrix = Rm @ self.matrix
        return self

    def rotate_about_axis(self, axis: ArbitraryAxis, angle_deg: float):
        """Prepend a rotation about an arbitrary axis (defined by a point and direction).

        The operation is equivalent to:
            1) translate(-axis.point)      # move axis point to origin
            2) rotate(axis.vector, angle)
            3) translate(axis.point)       # move back
        """
        # Translate so axis.point moves to the origin
        T_forward = np.eye(4)
        T_forward[:3, 3] = -axis.point

        # Rotation about the (now-origin) axis.direction
        rot = R.from_rotvec(np.deg2rad(angle_deg) * axis.vector)
        Rm = np.eye(4)
        Rm[:3, :3] = rot.as_matrix()

        # Translate back to original position
        T_back = np.eye(4)
        T_back[:3, 3] = axis.point

        # Combined transformation: back * rotation * forward
        combined = T_back @ Rm @ T_forward
        self.matrix = combined @ self.matrix
        return self

    def inverse(self):
        """Return a new Transformation equal to the inverse of this transformation."""
        inv = Transformation()
        inv.matrix = np.linalg.inv(self.matrix)
        return inv

    def reset(self):
        """Reset the transformation matrix to the identity."""
        self.matrix = np.eye(4)
        return self

    # ------------------------
    # Application to points
    # ------------------------

    def apply(self, points: np.ndarray) -> np.ndarray:
        """Apply the transformation to an array of 3D points.

        Parameters
        ----------
        points : ndarray, shape (n, 3)
            Points to transform.

        Returns
        -------
        ndarray, shape (n, 3)
            Transformed points.

        Raises
        ------
        ValueError
            If points is not an (n, 3) array.
        """
        points = np.asarray(points, dtype=float)
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("Points must have shape (n, 3).")

        # Convert to homogeneous coordinates, apply matrix, convert back
        hom = np.hstack([points, np.ones((points.shape[0], 1))])
        transformed = (self.matrix @ hom.T).T
        return transformed[:, :3]

    def __repr__(self) -> str:
        return f"Transformation(\n{self.matrix}\n)"


    # ------------------------
    # Static utility functions
    # ------------------------
    # Align a set of 2 points to another set of 2 points using rigid transformation
    @staticmethod
    def geom_2v_onto_2v(src1, src2, dst1, dst2):
        """
        Compute a transformation that superimposes src1 onto dst1 and aligns
        the line src1->src2 with the line dst1->dst2.
        
        After applying the transformation:
        - src1 coincides with dst1
        - src1, src2, dst1, dst2 all lie on the same line

        Examples:
        T = Transformation.geom_2v_onto_2v(src1, src2, dst1, dst2)
        pts = np.array([src1, src2])
        transformed_pts = T.apply(pts)
        print("Transformed src1, src2:")
        print(transformed_pts)
        """
        src1, src2, dst1, dst2 = map(lambda p: np.asarray(p, dtype=float), (src1, src2, dst1, dst2))
        
        # Step 1: Translate src1 → dst1
        translation_vec = dst1 - src1

        # Step 2: Compute direction vectors (unit)
        v_src = src2 - src1
        v_dst = dst2 - dst1
        n_src = np.linalg.norm(v_src)
        n_dst = np.linalg.norm(v_dst)
        if n_src == 0 or n_dst == 0:
            raise ValueError("Source and destination vectors must not be zero length.")
        v_src /= n_src
        v_dst /= n_dst

        # Step 3: Find rotation aligning v_src → v_dst
        cross = np.cross(v_src, v_dst)
        dot = np.dot(v_src, v_dst)
        if np.allclose(cross, 0):  # parallel or anti-parallel
            if dot > 0:
                rot_mat = np.eye(3)
            else:
                # 180° rotation around any perpendicular axis
                # choose an axis orthogonal to v_src
                perp = np.array([1, 0, 0])
                if np.allclose(np.abs(v_src), np.abs(perp)):
                    perp = np.array([0, 1, 0])
                axis = np.cross(v_src, perp)
                axis /= np.linalg.norm(axis)
                rot_mat = R.from_rotvec(np.pi * axis).as_matrix()
        else:
            axis = cross / np.linalg.norm(cross)
            angle = np.arccos(np.clip(dot, -1.0, 1.0))
            rot_mat = R.from_rotvec(angle * axis).as_matrix()

        # Step 4: Build full transformation matrix (rotate around dst1)
        T = np.eye(4)
        T[:3, 3] = translation_vec        # initial translation src1→dst1

        # Now rotate around dst1
        Rm = np.eye(4)
        Rm[:3, :3] = rot_mat
        T_back = np.eye(4)
        T_back[:3, 3] = dst1
        T_fwd = np.eye(4)
        T_fwd[:3, 3] = -dst1

        combined = T_back @ Rm @ T_fwd @ T  # translate, then rotate around dst1

        tr = Transformation()
        tr.matrix = combined
        return tr

    @staticmethod
    def geom_3v_onto_3v(src1, src2, src3, dst1, dst2, dst3):
        """
        Compute a rigid-body transformation (rotation + translation)
        that maps 3 source points onto 3 destination points.

        src1 -> dst1
        src2 direction -> dst2 direction
        src3 plane -> dst3 plane

        Raises
        ------
        ValueError
            If any pair of points used to define an axis are coincident or if the
            three points are colinear (cannot form a basis).
        """
        src1, src2, src3, dst1, dst2, dst3 = map(lambda p: np.asarray(p, dtype=float),
                                                  (src1, src2, src3, dst1, dst2, dst3))

        def make_frame(p1, p2, p3, label):
            v1 = p2 - p1
            v2 = p3 - p1
            n1 = np.linalg.norm(v1)
            if n1 == 0:
                raise ValueError(f"{label}: first and second points are identical or too close.")
            e1 = v1 / n1

            cross = np.cross(v1, v2)
            cross_norm = np.linalg.norm(cross)
            tol = 1e-8
            if cross_norm < tol:
                raise ValueError(f"{label}: points are collinear or degenerate; cannot form a basis.")
            e3 = cross / cross_norm

            e2 = np.cross(e3, e1)
            e2_norm = np.linalg.norm(e2)
            if e2_norm == 0:
                raise ValueError(f"{label}: degenerate basis computed; cannot form a basis.")
            e2 /= e2_norm

            Rf = np.column_stack((e1, e2, e3))  # rotation matrix (columns = axes)
            return Rf, p1

        R_src, O_src = make_frame(src1, src2, src3, "src")
        R_dst, O_dst = make_frame(dst1, dst2, dst3, "dst")

        # Rotation from source to destination frame
        Rm = R_dst @ R_src.T

        # Translation: after rotation, src1 should move to dst1
        t = O_dst - Rm @ O_src

        # Build full 4x4 transformation matrix
        M = np.eye(4)
        M[:3, :3] = Rm
        M[:3, 3] = t

        T = Transformation()
        T.matrix = M
        return T
    

def swing_atoms(
    axis_p1: np.ndarray,
    axis_p2: np.ndarray,
    atom_coords: np.ndarray,
    angle_deg: float
) -> np.ndarray:
    """
    Rotate (swing) a set of atom coordinates around an arbitrary axis by a specified angle.
    The axis of rotation is defined by two points in 3D space, `axis_p1` and `axis_p2`.
    Each atom in `atom_coords` is rotated by `angle_deg` degrees about this axis.
    Parameters
    ----------
    axis_p1 : array-like, shape (3,)
        First point defining the axis of rotation.
    axis_p2 : array-like, shape (3,)
        Second point defining the axis of rotation.
    atom_coords : array-like, shape (N, 3)
        Coordinates of the atoms to be rotated. Should be convertible to a NumPy array of shape (N, 3).
    angle_deg : float
        Angle in degrees by which to rotate the atoms around the axis.
    Returns
    -------
    new_coords : ndarray, shape (N, 3)
        The rotated coordinates of the atoms.

    Raises
    ------
    ValueError
        If `axis_p1` and `axis_p2` are identical, resulting in a zero vector for the axis direction.
    Examples
    --------
    >>> import numpy as np
    >>> from pymcce.utils import swing_atoms
    >>> atoms = np.array([[1.0, 0.0, 0.0],
    ...                   [0.0, 1.0, 0.0]])
    >>> axis_p1 = [0.0, 0.0, 0.0]
    >>> axis_p2 = [0.0, 0.0, 1.0]
    >>> angle = 90
    >>> new_atoms = swing_atoms(axis_p1, axis_p2, atoms, angle)
    >>> np.allclose(new_atoms, [[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])
    True
    """
    T = Transformation()
    axis_dir = axis_p2 - axis_p1
    arb_axis = ArbitraryAxis(point=axis_p1, direction=axis_dir)
    T.rotate_about_axis(arb_axis, angle_deg)
    new_coords = T.apply(atom_coords)
    return new_coords


def rotate_point_around_axis(p, axis_point1, axis_point2, angle_deg):
    """
    Rotate a point `p` around an arbitrary axis defined by two points
    `axis_point1` and `axis_point2` by a specified angle in degrees.

    Parameters
    ----------
    p : array-like, shape (3,)
        The point to be rotated.
    axis_point1 : array-like, shape (3,)
        First point defining the axis of rotation.
    axis_point2 : array-like, shape (3,)
        Second point defining the axis of rotation.
    angle_deg : float
        Angle in degrees to rotate the point around the axis.

    Returns
    -------
    rotated_p : ndarray, shape (3,)
        The rotated point coordinates.
    """
    p = np.asarray(p, dtype=float)
    axis_point1 = np.asarray(axis_point1, dtype=float)
    axis_point2 = np.asarray(axis_point2, dtype=float)

    T = Transformation()
    arb_axis = ArbitraryAxis(point=axis_point1, direction=axis_point2 - axis_point1)
    T.rotate_about_axis(arb_axis, angle_deg)
    rotated_p = T.apply(p.reshape(1, 3)).flatten()
    return rotated_p


@njit
def LJ_energy(coords, radii, epsilons, r_cut, sf_matrix):
    """
    Compute Lennard-Jones energy using linked cell list for efficiency.

    Parameters:
    coords : ndarray, shape (n, 3)
        Atomic coordinates.
    radii : ndarray, shape (n,)
        Atomic Lennard-Jones radii. This is sigma in the LJ formula. sigma = Rmin/2^(1/6), must be converted outside.
    epsilons : ndarray, shape (n,)
        Atomic Lennard-Jones epsilon values.
    r_cut : float
        Cutoff distance for interactions.
    sf_matrix : ndarray, shape (n, n)
        Screening factor matrix.

    Returns:
    float
        Total Lennard-Jones energy.
    """
    n = coords.shape[0]
    r_cut2 = r_cut * r_cut

    # Determine bounding box
    box_min = np.empty(3, dtype=np.float32)
    box_max = np.empty(3, dtype=np.float32)
    for d in range(3):
        c = coords[:, d]
        box_min[d] = c.min()
        box_max[d] = c.max()

    # Padding so cell list works properly
    pad = r_cut + 1e-8
    box_min[0] -= pad
    box_min[1] -= pad
    box_min[2] -= pad
    box_max[0] += pad
    box_max[1] += pad
    box_max[2] += pad

    box = box_max - box_min

    # Number of cells along each axis
    nx = int(box[0] / r_cut)
    ny = int(box[1] / r_cut)
    nz = int(box[2] / r_cut)
    nx = max(nx, 1)
    ny = max(ny, 1)
    nz = max(nz, 1)

    n_cells = nx * ny * nz

    # Linked cell structures
    head = -np.ones(n_cells, dtype=np.int32)
    linked_list = -np.ones(n, dtype=np.int32)

    # Assign atoms to cells
    for i in range(n):
        cx = int((coords[i, 0] - box_min[0]) / r_cut)
        cy = int((coords[i, 1] - box_min[1]) / r_cut)
        cz = int((coords[i, 2] - box_min[2]) / r_cut)

        cx = min(max(cx, 0), nx - 1)
        cy = min(max(cy, 0), ny - 1)
        cz = min(max(cz, 0), nz - 1)

        cell = cx + nx * (cy + ny * cz)
        linked_list[i] = head[cell]
        head[cell] = i

    # LJ computation
    total_E = 0.0

    for cz in range(nz):
        for cy in range(ny):
            for cx in range(nx):
                cell = cx + nx * (cy + ny * cz)
                i_atom = head[cell]

                while i_atom != -1:

                    # Loop over 27 neighbor cells
                    for dz in (-1, 0, 1):
                        z2 = cz + dz
                        if z2 < 0 or z2 >= nz:
                            continue
                        for dy in (-1, 0, 1):
                            y2 = cy + dy
                            if y2 < 0 or y2 >= ny:
                                continue
                            for dx in (-1, 0, 1):
                                x2 = cx + dx
                                if x2 < 0 or x2 >= nx:
                                    continue

                                neighbor_cell = x2 + nx * (y2 + ny * z2)
                                j_atom = head[neighbor_cell]

                                while j_atom != -1:
                                    if j_atom > i_atom:

                                        # Distance
                                        dx_dist = coords[i_atom, 0] - coords[j_atom, 0]
                                        dy_dist = coords[i_atom, 1] - coords[j_atom, 1]
                                        dz_dist = coords[i_atom, 2] - coords[j_atom, 2]
                                        r2 = dx_dist*dx_dist + dy_dist*dy_dist + dz_dist*dz_dist

                                        # Cutoff check
                                        if r2 < r_cut2:

                                            sf = sf_matrix[i_atom, j_atom]
                                            if sf > 0.0:

                                                # Lorentz-Berthelot (σ_ij, ε_ij)
                                                sigma = 0.5 * (radii[i_atom] + radii[j_atom])
                                                epsilon = np.sqrt(epsilons[i_atom] *
                                                                  epsilons[j_atom])

                                                inv = (sigma * sigma) / r2
                                                inv6 = inv * inv * inv
                                                inv12 = inv6 * inv6

                                                total_E += sf * 4.0 * epsilon * (inv12 - inv6)

                                    j_atom = linked_list[j_atom]

                    i_atom = linked_list[i_atom]

    return total_E

# Use LJ_energy_pairwise_vectorized for speed
def LJ_energy_pairwise(coords_group1, radii_group1, epsilons_group1,
              coords_group2, radii_group2, epsilons_group2,
              r_cut, sf_matrix):
    # σ and ε values are in angstroms and kJ/mol
    # Lorentz-Berthelot combining rules:
    #   Standard: σij = 0.5*(σi + σj)
    #   Here: input radii are already R_min/2, so σij = radii_i + radii_j (each radius is half the minimum distance parameter)
    #   ϵij = sqrt(ϵi * ϵj)
    #   p_lj = ϵij[(σij/r)^12 - 2(σij/r)^6]
    #   σij is the distance where LJ potential reaches minimum: -ϵij
    # r is the atom distance
    n1 = coords_group1.shape[0]
    n2 = coords_group2.shape[0]
    r_cut2 = r_cut * r_cut  # use squared distance for efficiency
    energy = 0.0
    
    for i in range(n1):
        for j in range(n2):
            dx = coords_group1[i, 0] - coords_group2[j, 0]
            dy = coords_group1[i, 1] - coords_group2[j, 1]
            dz = coords_group1[i, 2] - coords_group2[j, 2]
            r2 = dx*dx + dy*dy + dz*dz
            
            if r2 < r_cut2:
                sigma = radii_group1[i] + radii_group2[j]
                epsilon = np.sqrt(epsilons_group1[i] * epsilons_group2[j])
                inv_r2 = (sigma * sigma) / r2
                inv_r6 = inv_r2**3
                inv_r12 = inv_r6**2
                lj = epsilon * (inv_r12 - 2 * inv_r6)
                energy += sf_matrix[i, j] * lj
    
    return energy

@njit
def LJ_energy_pairwise_vectorized(coords_group1, radii_group1, epsilons_group1,
                                  coords_group2, radii_group2, epsilons_group2,
                                  r_cut, sf_matrix):
    """
    Compute Lennard-Jones interaction energy between two groups of atoms
    using explicit loops for Numba optimization.
    """
    n1 = coords_group1.shape[0]
    n2 = coords_group2.shape[0]
    r_cut2 = r_cut * r_cut
    energy = 0.0
    eps = 1e-12
    for i in range(n1):
        for j in range(n2):
            dx = coords_group1[i, 0] - coords_group2[j, 0]
            dy = coords_group1[i, 1] - coords_group2[j, 1]
            dz = coords_group1[i, 2] - coords_group2[j, 2]
            r2 = dx*dx + dy*dy + dz*dz
            if r2 < r_cut2:
                sigma = radii_group1[i] + radii_group2[j]
                epsilon = np.sqrt(epsilons_group1[i] * epsilons_group2[j])
                r2_safe = r2 + eps
                inv_r2 = (sigma * sigma) / r2_safe
                inv_r6 = inv_r2**3
                inv_r12 = inv_r6**2
                lj = epsilon * (inv_r12 - 2 * inv_r6)
                energy += sf_matrix[i, j] * lj
    return energy

vdw_pairwise = LJ_energy_pairwise_vectorized  # alias for clarity in use


def gram_schmidt(vectors):
    """Orthonormalize a set of vectors using Gram-Schmidt."""
    basis = []
    for v in vectors:
        w = v.copy()
        for b in basis:
            w -= np.dot(w, b) * b
        norm = np.linalg.norm(w)
        if norm < 1e-12:
            raise ValueError(
                "Input vectors are linearly dependent or nearly linearly dependent; "
                "cannot construct an orthonormal basis."
            )
        w /= norm
        basis.append(w)
    return basis


def sp3_3known(v0, v1, v2, v3):
    """
    Given the center atom and three known points v0, v1, v2, v3, 
    compute the coordinates of the unknown point in 3D space.

    Parameters
    ----------
    v0 : array-like, shape (3,)
        Coordinates of the center point.
    v1 : array-like, shape (3,)
        Coordinates of the first known point.
    v2 : array-like, shape (3,)
        Coordinates of the second known point.
    v3 : array-like, shape (3,)
        Coordinates of the third known point.

    Returns
    -------
    np.ndarray, shape (3,)
        Coordinates of the unknown point.

    Raises
    ------
    ValueError
        If the provided points are collinear or if no valid solution exists.

    Notes
    -----
    This function uses trilateration to determine the position of the unknown point.
    """
    # v4 is located at distance BOND_DISTANCE_H from v0 in the opposite direction of the average of unit vector from v0 to v1, v2, v3
    v0 = np.array(v0, dtype=float)
    v1 = np.array(v1, dtype=float)
    v2 = np.array(v2, dtype=float)
    v3 = np.array(v3, dtype=float)
    dir1 = (v1 - v0) / np.linalg.norm(v1 - v0)
    dir2 = (v2 - v0) / np.linalg.norm(v2 - v0)
    dir3 = (v3 - v0) / np.linalg.norm(v3 - v0)
    avg_dir = (dir1 + dir2 + dir3) / np.linalg.norm(dir1 + dir2 + dir3)
    v4 = v0 - BOND_DISTANCE_H * avg_dir

    return np.array([v4])

def sp3_2known(v0, v1, v2):
    """
    Given the center atom and two known points v0, v1, v2, 
    compute the coordinates of the unknown two points in 3D space.

    Parameters
    ----------
    v0 : array-like, shape (3,)
        Coordinates of the center point.
    v1 : array-like, shape (3,)
        Coordinates of the first known point.
    v2 : array-like, shape (3,)
        Coordinates of the second known point.

    Returns
    -------
    np.ndarray, shape (2, 3)
        Coordinates of the unknown two points.

    Raises
    ------
    ValueError
        If the provided points are collinear or if no valid solution exists.

    """
    # Place v0 at center, v1 and v2 on vertices of tetrahedron, compute v3 and v4
    v0 = np.array(v0, dtype=float)
    v1 = np.array(v1, dtype=float)
    v2 = np.array(v2, dtype=float)
    
    # Step 1: Normalize directions from center
    dir1 = (v1 - v0) / np.linalg.norm(v1 - v0)
    dir2 = (v2 - v0) / np.linalg.norm(v2 - v0)

    # Step 2: Construct initial candidate vectors
    bisector = dir1 + dir2           # will be orthonormalized
    normal = np.cross(dir1, dir2)    # will be orthonormalized

    # Step 3: Apply Gram–Schmidt
    bisector, normal = gram_schmidt([bisector, normal])

    # Step 4: Coefficients for tetrahedral geometry
    angle = np.arccos(-1.0 / 3.0)  # ~109.47 degrees
    a = np.cos(angle/2)
    c = np.sin(angle/2)

    # Step 5: Compute remaining two vertices
    v3 = v0 - BOND_DISTANCE_H * (a * bisector + c * normal)
    v4 = v0 - BOND_DISTANCE_H * (a * bisector - c * normal)

    return np.array([v3, v4])

def sp3_1known(v0, v1):
    """
    Given the center atom and one known point v0, v1, 
    compute the coordinates of the unknown three points in 3D space.

    Parameters
    ----------
    v0 : array-like, shape (3,)
        Coordinates of the center point.
    v1 : array-like, shape (3,)
        Coordinates of the first known point.

    Returns
    -------
    np.ndarray, shape (3, 3)
        Coordinates of the unknown three points.

    Raises
    ------
    ValueError
        If no valid solution exists.

    """
    # Place v0 at center, v1 on vertex of tetrahedron, compute v2, v3, v4
    v0 = np.array(v0, dtype=float)
    v1 = np.array(v1, dtype=float)

    # Step 1: Normalize direction from center
    diff = v1 - v0
    norm = np.linalg.norm(diff)
    if norm == 0.0:
        raise ValueError("v0 and v1 must be distinct points to define a direction.")
    dir1 = diff / norm

    # Step 2: Construct initial candidate vectors
    arbitrary = np.array([1.0, 0.0, 0.0])
    if np.allclose(dir1, arbitrary):
        arbitrary = np.array([0.0, 1.0, 0.0])
    normal1 = np.cross(dir1, arbitrary)
    normal2 = np.cross(dir1, normal1)

    # Step 3: Apply Gram–Schmidt
    normal1, normal2 = gram_schmidt([normal1, normal2])

    # Step 4: Coefficients for tetrahedral geometry
    angle = np.arccos(-1.0 / 3.0)  # ~109.47 degrees
    a = np.cos(angle)
    c = np.sin(angle)

    # Step 5: Compute remaining three vertices
    v2 = v0 + BOND_DISTANCE_H * (a * dir1 + c * normal1)
    v3 = v0 + BOND_DISTANCE_H * (a * dir1 - c * (0.5 * normal1 + (np.sqrt(3)/2) * normal2))
    v4 = v0 + BOND_DISTANCE_H * (a * dir1 - c * (0.5 * normal1 - (np.sqrt(3)/2) * normal2))

    return np.array([v2, v3, v4])

def sp3_0known(v0):
    """
    Given the center atom v0, compute the coordinates of the four points
    in a tetrahedral geometry around v0.

    Parameters
    ----------
    v0 : array-like, shape (3,)
        Coordinates of the center point.

    Returns
    -------
    np.ndarray, shape (4, 3)
        Coordinates of the four points.

    Raises
    ------
    ValueError
        If no valid solution exists.

    """
    v0 = np.array(v0, dtype=float)

    # Predefined tetrahedral directions
    directions = np.array([
        [ 1,  1,  1],
        [ 1, -1, -1],
        [-1,  1, -1],
        [-1, -1,  1]
    ], dtype=float)
    directions /= np.linalg.norm(directions[0])  # normalize
    points = [v0 + BOND_DISTANCE_H * dir_vec for dir_vec in directions]

    return np.array(points)

def sp2_2known(v0, v1, v2):
    """
    Given the center atom and two known points v0, v1, v2, 
    compute the coordinates of the unknown point in 3D space
    in a trigonal planar geometry.

    Parameters
    ----------
    v0 : array-like, shape (3,)
        Coordinates of the center point.
    v1 : array-like, shape (3,)
        Coordinates of the first known point.
    v2 : array-like, shape (3,)
        Coordinates of the second known point.

    Returns
    -------
    np.ndarray, shape (1, 3)
        Coordinates of the unknown point.

    Raises
    ------
    ValueError
        If the provided points are collinear or if no valid solution exists.

    """
    v0 = np.array(v0, dtype=float)
    v1 = np.array(v1, dtype=float)
    v2 = np.array(v2, dtype=float)

    # Step 1: Normalize directions from center
    d1 = v1 - v0
    d2 = v2 - v0
    norm_d1 = np.linalg.norm(d1)
    norm_d2 = np.linalg.norm(d2)
    if norm_d1 == 0.0:
        raise ValueError("v1 coincides with v0; direction vector has zero length.")
    if norm_d2 == 0.0:
        raise ValueError("v2 coincides with v0; direction vector has zero length.")
    u1 = d1 / norm_d1
    u2 = d2 / norm_d2

    # Step 2: Compute bisector and normal
    opposite_bisector = -(u1 + u2)
    norm_opposite = np.linalg.norm(opposite_bisector)
    if norm_opposite == 0.0:
        raise ValueError(
            "Provided points are collinear or symmetric around v0; no valid bisector exists."
        )

    # Step 3: Compute remaining vertex
    v3 = v0 + BOND_DISTANCE_H * (opposite_bisector / norm_opposite)

    return np.array([v3])

def sp2_1known(v0, v1, v1e):
    """
    	v3 v2
    	  | /
    	   v0
    	   |
    	   v1
    	   /
    	  v1e
    
    v0 is sp2 type.
    v0, v1, v1e's coordinates are known.
    v3, v4's coordinates are to be determined.    
    We need to know one more atom connected to v1 in order to determine the plane. The returned v3 and v4 will be in the
    order that v3 is the cis position to the heaviest known atom connected to v1.

    If v1e is None, then we just assume an arbitrary plane.

    Parameters
    ----------
    v0 : array-like, shape (3,)
        Coordinates of the center point.
    v1 : array-like, shape (3,)
        Coordinates of the first known point.
    v1e : array-like, shape (3,) or None
        Coordinates of an extra point connected to v1 to define the plane.

    Returns
    -------
    np.ndarray, shape (2, 3)
        Coordinates of the unknown two points.

    Raises
    ------
    ValueError
        If no valid solution exists.

    """
    v0 = np.array(v0, dtype=float)
    v1 = np.array(v1, dtype=float)
    v1e = np.array(v1e, dtype=float) if v1e is not None else None

    # Step 1: Normalize direction from center
    u1 = (v1 - v0) / np.linalg.norm(v1 - v0)
    u1e = (v1e - v1) / np.linalg.norm(v1e - v1) if v1e is not None else None

    # Step 2: Compute normal to the plane defined by v0, v1, v1e
    if v1e is not None:
        normal = np.cross(u1, u1e)
        normal /= np.linalg.norm(normal)
    else:
        # Arbitrary normal if no extra atom is provided
        arbitrary = np.array([1.0, 0.0, 0.0])
        if np.allclose(u1, arbitrary):
            arbitrary = np.array([0.0, 1.0, 0.0])
        normal = np.cross(u1, arbitrary)
        normal /= np.linalg.norm(normal)

    # Step 3: Compute perpendicular direction in the plane
    perp = np.cross(normal, u1)
    perp /= np.linalg.norm(perp)

    # Step 4: Compute remaining two vertices at 120 degrees apart
    angle = 120.0 * (np.pi / 180.0)  # Convert to radians
    a = np.cos(angle)
    c = np.sin(angle)
    v2 = v0 + BOND_DISTANCE_H * (a * u1 + c * perp)
    v3 = v0 + BOND_DISTANCE_H * (a * u1 - c * perp)

    return np.array([v2, v3])

def sp2_0known(v0):
    """
    Given the center atom v0, compute the coordinates of the three points
    in a trigonal planar geometry around v0.

    Parameters
    ----------
    v0 : array-like, shape (3,)
        Coordinates of the center point.

    Returns
    -------
    np.ndarray, shape (3, 3)
        Coordinates of the three points.

    Raises
    ------
    ValueError
        If no valid solution exists.

    """
    v0 = np.array(v0, dtype=float)

    # Predefined trigonal planar directions
    directions = np.array([
        [ 1,  0,  0],
        [-0.5,  np.sqrt(3)/2,  0],
        [-0.5, -np.sqrt(3)/2,  0]
    ], dtype=float)
    directions /= np.linalg.norm(directions[0])  # normalize
    points = [v0 + BOND_DISTANCE_H * dir_vec for dir_vec in directions]

    return np.array(points)

def sp_1known(v0, v1):
    """
    Given the center atom and one known point v0, v1, 
    compute the coordinates of the unknown point in 3D space
    in a linear geometry.

    Parameters
    ----------
    v0 : array-like, shape (3,)
        Coordinates of the center point.
    v1 : array-like, shape (3,)
        Coordinates of the first known point.

    Returns
    -------
    np.ndarray, shape (1, 3)
        Coordinates of the unknown point.

    Raises
    ------
    ValueError
        If no valid solution exists.

    """
    v0 = np.array(v0, dtype=float)
    v1 = np.array(v1, dtype=float)

    # Step 1: Normalize direction from center
    dir1 = (v1 - v0) / np.linalg.norm(v1 - v0)

    # Step 2: Compute remaining vertex in opposite direction
    v2 = v0 - BOND_DISTANCE_H * dir1

    return np.array([v2])