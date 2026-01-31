import numpy as np


def hdot(arr1: np.ndarray, arr2: np.ndarray, inshape: tuple[int, ...]) -> float:
    axis = tuple(range(-len(inshape), 0))
    axis2 = tuple(range(-(len(inshape) - 1), 0))

    dotprod = 2 * np.sum(np.conj(arr1) * arr2, axis=axis) - np.sum(
        np.conj(arr1[..., 0]) * arr2[..., 0], axis=axis2
    )

    if inshape[-1] % 2 == 0:
        dotprod -= np.sum(np.conj(arr1[..., -1]) * arr2[..., -1], axis=axis2)

    return np.real(dotprod)


def hnorm(inarray: np.ndarray, inshape: tuple[int, ...]) -> float:
    r"""Hermitian l2-norm of array in discrete Fourier space.

    Compute the l2-norm of complex array

    .. math::

       \|x\|_2 = \sqrt{\sum_{n=1}^{N} |x_n|^2}

    considering the Hermitian property. Must be used with `rdftn`. Equivalent of
    `np.linalg.norm` for array applied on full Fourier space array (those
    obtained with `dftn`).

    Parameters
    ----------
    inarray : array-like of shape (... + inshape)
        The input array with half of the Fourier plan.

    inshape: tuple of int
        The shape of the original array `oarr` where `inarray=rdft(oarr)`.

    Returns
    -------
    norm : float

    """
    axis = tuple(range(-len(inshape), 0))
    axis2 = tuple(range(-(len(inshape) - 1), 0))
    norm = 2 * np.sum(np.abs(inarray) ** 2, axis=axis) - np.sum(
        np.abs(inarray[..., 0]) ** 2, axis=axis2
    )
    if inshape[-1] % 2 == 0:
        norm -= np.sum(np.abs(inarray[..., -1]) ** 2, axis=axis2)

    return np.sqrt(norm)


def value_residual(arr, sm, residual):
    return np.sum(arr * (-sm - residual)) / 2


def value_residualf(arr, sm, residual):
    return np.real(np.sum(np.conj(arr) * (-sm - residual))) / 2
    # return np.real(np.sum(arr * (-sm - residual))) / 2


def value_residualhf(arr, sm, residual, shape):
    # return (np.sum(np.conj(arr) * (-second_memberf - residual))) / 2
    return hdot(arr, -sm - residual, shape) / 2


# def value_residualf2(arr, residual):
#     return np.vdot(arr.ravel(), (-second_memberf - residual).ravel()) / 2


shape = (256, 256)
arr = np.random.standard_normal(shape)
arrf = np.fft.fft2(arr, norm="ortho")
res = np.random.uniform(size=shape)
resf = np.fft.fft2(res, norm="ortho")
sm = np.random.poisson(size=shape)
smf = np.fft.fft2(sm, norm="ortho")

print(value_residual(arr, sm, res))
print(value_residualf(arr, sm, res))
print(value_residualhf(arrf, smf, resf, shape))
