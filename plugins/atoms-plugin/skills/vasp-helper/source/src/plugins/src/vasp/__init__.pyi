from vasp._force_and_stress import *
from vasp._local_potential import *
from vasp._machine_learning import *
from vasp._mpi_grid import *
from vasp._neighbors import *
from vasp._occupations import *
from vasp._structure import *
from vasp import typing

SUCCESS = 0  # This is the code indicating no error occurred
ERROR_IN_PLUGIN = 3  # This is the same error code defined in the C++ file.

def fft_forward(data: typing.DoubleArray) -> None:
    """Perform a forward Fast Fourier Transform (FFT) on the input data in distrubut format inplace.

    Parameters
    ----------
    data : DoubleArray
        The input data to be transformed.
        The shape should be exactly the same as the shape of the grid used in the VASP calculations.
        If grid shape is (nx, ny, nz), the input data should be (ncol, nz + 2).

    Notes
    -----
    This function is typically used in computational physics and materials science
    for analyzing periodic systems and performing operations in reciprocal space.
    """
    ...

def fft_backward(data: typing.ComplexArray) -> None:
    """Perform an inverse Fast Fourier Transform (FFT) on the input data in distrubut format inplace.

    Parameters
    ----------
    data : DoubleArray
        The input data to be transformed.
        The shape should be exactly the same as the shape of the grid used in the VASP calculations.
        Since reciprocal space is in RC format, the reciprocal grid is ((nz + 2) // 2, ny, nx) of complex array
        If grid shape is (nx, ny, nz), the input data should be (ncol, nx).

    Notes
    -----
    This function is typically used in computational physics and materials science
    for analyzing periodic systems and performing operations in reciprocal space.
    """
    ...
