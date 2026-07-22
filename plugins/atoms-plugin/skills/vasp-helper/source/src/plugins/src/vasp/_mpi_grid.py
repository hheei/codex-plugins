import functools

import numpy as np
from mpi4py import MPI

__all__ = (
    "build_rl_idx",
    "build_rc_idx",
    "merge_rl_root",
    "merge_rc_root",
)


def _normalize_shape(global_shape) -> tuple[int, int, int]:
    shape = np.asarray(global_shape).reshape(-1)
    if shape.size != 3:
        raise ValueError("global_shape must contain exactly three elements")
    return tuple(int(v) for v in shape.tolist())


@functools.lru_cache(maxsize=None)
def _build_rl_idx_cached(
    global_shape: tuple[int, int, int],
    plane_wise: bool,
    ncpu: int,
    rank: int,
) -> tuple[np.ndarray, np.ndarray]:
    NGX, NGY, _ = global_shape
    if plane_wise:
        # Matches REAL_STDLAY plane-wise ownership:
        # NODE_TARGET = MOD(x-1, NCPU)+1 in 1-based form.
        # Here x is 0-based, so we use (x % ncpu) == rank.
        x = np.arange(NGX, dtype=np.int64)
        y = np.arange(NGY, dtype=np.int64)
        xx, yy = np.meshgrid(x, y, indexing="xy")  # shape (NGY, NGX), y outer, x inner
        mask = (xx % ncpu) == rank
        I2 = xx[mask]  # x
        I3 = yy[mask]  # y
    else:
        # Matches REAL_STDLAY round-robin ownership:
        # NODE_TARGET = MOD(IND, NCPU)+1 in 1-based form.
        total = NGX * NGY
        local_ind = np.arange(rank, total, ncpu, dtype=np.int64)
        I2 = local_ind % NGX  # x
        I3 = local_ind // NGX  # y
    return I2, I3


@functools.lru_cache(maxsize=None)
def _build_rc_idx_cached(
    global_shape: tuple[int, int, int],
    ncpu: int,
    rank: int,
) -> tuple[np.ndarray, np.ndarray]:
    _, NGY, NGZ = global_shape
    # NGZ here is NGZ_half (for example, 50 -> 26 after r2c on z).
    total = NGY * NGZ
    local_ind = np.arange(rank, total, ncpu)  # global 0-based flattened column index
    # Inverse map from flattened column id to (y, z_half).
    I2 = local_ind % NGY
    I3 = local_ind // NGY
    return I2, I3


def build_rl_idx(
    global_shape, plane_wise: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build RL column indices for the current MPI rank (Python 0-based).

    Inputs:
        global_shape (tuple[int, int, int]): (NGX, NGY, NGZ) global real-space grid.
        plane_wise (bool): If True, use plane-wise ownership rule; otherwise round-robin.

    Outputs:
        tuple[np.ndarray, np.ndarray]:
            I2 (int32): local x isndices, shape (ncol_local,), 0-based.
            I3 (int32): local y indices, shape (ncol_local,), 0-based.

    Notes:
        - RL columns are keyed by (x, y), each column has length NGZ along z.
        - Returned length equals local RL column count on this rank.
    """
    comm = MPI.COMM_WORLD
    ncpu = comm.Get_size()
    rank = comm.Get_rank()  # 0-based
    shape = _normalize_shape(global_shape)
    I2, I3 = _build_rl_idx_cached(shape, bool(plane_wise), ncpu, rank)
    return I2.copy(), I3.copy()


def build_rc_idx(global_shape) -> tuple[np.ndarray, np.ndarray]:
    """
    Build RC column indices for the current MPI rank (Python 0-based).

    Inputs:
        global_shape (tuple[int, int, int]): (NGX, NGY, NGZ_half), where NGZ_half = NGZ//2+1.

    Outputs:
        tuple[np.ndarray, np.ndarray]:
            IC2 (int64): local y indices, shape (ncol_local,), 0-based.
            IC3 (int64): local z_half indices, shape (ncol_local,), 0-based.

    Notes:
        - RC columns are keyed by (y, z_half), each column has length NGX along x.
        - Ownership follows REC_STDLAY round-robin over flattened (z_half, y) columns.
    """
    comm = MPI.COMM_WORLD
    ncpu = comm.Get_size()
    rank = comm.Get_rank()  # 0-based

    shape = _normalize_shape(global_shape)
    I2, I3 = _build_rc_idx_cached(shape, ncpu, rank)
    return I2.copy(), I3.copy()


def merge_rl_root(values: np.ndarray, global_shape, plane_wise: bool = False):
    """
    Merge distributed RL local columns onto root rank.

    Inputs:
        values (np.ndarray): local 1D real buffer on each rank.
            Expected usable prefix length is ncol_local * NGZ.
        global_shape (tuple[int, int, int]): (NGX, NGY, NGZ).
        plane_wise (bool): ownership mode used by RL indexing.

    Outputs:
        np.ndarray | None:
            - On root: merged real grid, shape (NGX, NGY, NGZ), dtype float64.
            - On non-root ranks: None.
    """
    comm = MPI.COMM_WORLD

    I2, I3 = build_rl_idx(global_shape, plane_wise=plane_wise)
    NGX, NGY, NGZ = _normalize_shape(global_shape)

    values = np.reshape(values, (-1,), copy=False)

    # Keep only valid RL payload: ncol_local * NGZ.
    # This avoids passing padding/unused tail.
    all_vals = comm.gather(values[: len(I2) * NGZ], root=0)
    all_i2 = comm.gather(I2, root=0)
    all_i3 = comm.gather(I3, root=0)

    if comm.rank != 0:
        return None

    merged = np.empty((NGX, NGY, NGZ), dtype=np.float64)
    for vals, i2, i3 in zip(all_vals, all_i2, all_i3):
        # vals: (ncol_local*NGZ,) -> (ncol_local, NGZ)
        # Scatter local columns back to global coordinates (x=i2, y=i3, :).
        merged[i2, i3, :] = vals.reshape((len(i2), NGZ))
    return merged


def merge_rc_root(values: np.ndarray, global_shape):
    """
    Merge distributed RC local columns onto root rank.

    Inputs:
        values (np.ndarray): local RC buffer exposed by plugin, typically float64
            with interleaved real/imag parts (size ~ 2 * local_complex_count).
        global_shape (tuple[int, int, int]): (NGX, NGY, NGZ) in real-space terms.

    Outputs:
        np.ndarray | None:
            - On root: merged RC grid, shape (NGZ_half, NGY, NGX), dtype complex128.
            - On non-root ranks: None.

    Notes:
        - We first reinterpret local buffer with `.view(np.complex128)`.
        - RC coordinates are indexed as (z_half, y, x) in the output tensor.
    """
    comm = MPI.COMM_WORLD

    NGX, NGY, NGZ = _normalize_shape(global_shape)
    # r2c half-spectrum length on z.
    NGZH = (NGZ + 2) // 2
    I2, I3 = build_rc_idx((NGX, NGY, NGZH))

    all_vals = comm.gather(values.view(np.complex128), root=0)
    all_i2 = comm.gather(I2, root=0)
    all_i3 = comm.gather(I3, root=0)

    if comm.rank != 0:
        return None

    merged = np.empty((NGZH, NGY, NGX), dtype=np.complex128)

    for vals, i2, i3 in zip(all_vals, all_i2, all_i3):
        # vals: (ncol_local*NGX,) complex -> (ncol_local, NGX)
        # RC column key is (y=i2, z_half=i3), with x as the row direction.
        block = vals.reshape((len(i2), NGX))
        merged[i3, i2, :] = block

    return merged
