import numpy as np
from warnings import warn
import sys
sys.setrecursionlimit(100000)


def dsconv(
    x: np.ndarray,
    filters: np.ndarray,
    mode: str = "full",
    offset: int = 0,
    disable_jit: int = 0,
    use_parallel: bool = False,
):
    """
    Return down-sampled convolutions with ``filters``.
    ``filters`` is a 2d array of shape ``(K, F)`` where
    ``F`` represents the batch of filters.
    It first computes convolution with the filters.
    Then, it performs down-sampling (keep 1 every 2) on both convolution
    results (it is useful for Discrete-Wavelet-Transform).
    The fonction consider the second dimension of the input ``x``
    to be the batch size.
    ``offset`` (0 or 1) argument determines the first element to compute.
    The ouput ``y`` is equivalent to:

    .. code-block:: python

        import numpy as np
        c1 = np.convolve(x, filters[:, 0], mode)[offset::2]
        c2 = np.convolve(x, filters[:, 1], mode)[offset::2]
        y = np.hstack((c1, c2))

    Args:
        x: 2d array
            Input array of shape ``(N, batch)``.
        filters: 2d array
            The second dimension expects a batch of filters.
        mode: ``str``, optional
            - ``'full'`` computes convolution (input + padding).
            - ``'valid'`` computes ``'full'`` mode and extract centered output
              that does not depend on the padding.
            - ``'same'`` computes ``'full'`` mode and extract centered output
              that has the same shape that the input.
        offset: ``int``, optional
            First element to keep (default is 0).
        disable_jit: ``int``, optional
            If 0 (default) enable Numba jit.
        use_parallel: ``bool``, optional
            If True enable Numba ``prange``.
            ``False`` is default value.

    Returns:
        The concatenation of two down-sampled convolutions.

    Examples:
        >>> import numpy as np
        >>> from dsconv import dsconv
        >>> N = 1024
        >>> x = np.random.rand(N)
        >>> f = np.random.rand(32, 2)
        >>> c1 = dsconv(x.reshape(-1, 1), f, mode='same', offset=0)
        >>> c2 = np.convolve(x, f[:, 0], mode='same')
        >>> c3 = np.convolve(x, f[:, 1], mode='same')
        >>> np.allclose(c1.reshape(-1), np.hstack((c2[::2], c3[::2])))
        True

    .. seealso::
        `SciPy convolve function <https://docs.scipy.org/doc/scipy/
        reference/generated/scipy.signal.convolve.html>`_,
        `SciPy correlate function <https://docs.scipy.org/doc/scipy/
        reference/generated/scipy.signal.correlate.html>`_.
    """

    def njit(*args, **kwargs):
        def dummy(f):
            return f
        return dummy

    def prange(n):
        return range(n)

    try:
        import numba as nb
        from numba import njit, prange
        nb.config.THREADING_LAYER = "omp"
        T = nb.config.NUMBA_NUM_THREADS
        nb.config.DISABLE_JIT = disable_jit
    except ImportError:
        warn("Did not find Numba.")
        T = 1

    if mode not in ["full", "valid", "same"]:
        raise ValueError("mode is either 'full' (default), 'valid' or 'same'.")

    N = int(x.shape[0])

    if filters.ndim != 2:
        raise Exception("filters must a 2d array.")
    K = int(filters.shape[0])
    F = int(filters.shape[1])

    if K > N and mode == "valid":
        raise ValueError(
            "Size of the kernel is greater than the size"
            + " of the signal and mode is valid."
        )
    if offset != 0 and offset != 1:
        raise ValueError("offset must be either 0 or 1.")

    every = 2

    # Length of the output as a function of convolution mode
    n_out = N + (int(mode == 'full') - int(mode == 'valid')) * (K - 1)
    start = (N + K - 1 - n_out) // 2 + offset
    end = min(N + K - 1, start + n_out - offset)
    n_samples = int(np.ceil((n_out - offset) / every))
    if n_samples <= 0:
        raise Exception(
            "mode and offset values are incompatibles"
            + " with kernel and signal sizes."
        )

    perT = int(every * np.ceil(np.ceil((N + K - 1 - start) / T) / every))
    rperT = int(np.ceil(N / T))

    @njit(parallel=use_parallel, cache=True)
    def _numba_mm(x, filters):
        # x is always 2d
        batch_size = x.shape[1]
        if batch_size == 1:
            acc = np.empty((T, F), dtype=(filters[0, 0] * x[0, :]).dtype)
            y = np.empty((2 * n_samples, batch_size),
                         dtype=(filters[0, 0] * x[0, :]).dtype)
            for t in prange(T):
                for i in range(start + t * perT,
                               min(end, start + (t + 1) * perT),
                               every):
                    # i - j < N
                    # i - j >= 0
                    # j < K
                    acc[t, :] = 0
                    for j in range(max(0, i - N + 1), min(K, i + 1), 1):
                        for f in range(F):
                            acc[t, f] += filters[j, f] * x[i - j, 0]
                    for f in range(F):
                        y[f * n_samples + (i - start) // every, 0] = acc[t, f]
        else:
            tmp = np.empty((T, F), dtype=filters.dtype)
            y = np.zeros((2 * n_samples, batch_size),
                         dtype=(filters[0, 0] * x[0, :]).dtype)
            for t in prange(T):
                for i in range(start + t * perT,
                               min(end, start + (t + 1) * perT),
                               every):
                    # i - j < N
                    # i - j >= 0
                    # j < K
                    for j in range(max(0, i - N + 1), min(K, i + 1), 1):
                        # NumPy uses row-major format
                        for b in range(batch_size):
                            for f in range(F):
                                y[f * n_samples + (i - start) // every, b] += (
                                    filters[j, f] * x[i - j, b]
                                )
        return y

    @njit(parallel=use_parallel, cache=True)
    def _numba_rmm(x, filters):
        # x is always 2d
        batch_size = x.shape[1]
        a = 0 if mode == 'full' and offset == 0 else 1
        y = np.full((N, batch_size),
                    0.0 * (filters[0, 0] * x[0, 0]))
        for t in prange(T):
            for i in range(t * rperT, min(N, (t + 1) * rperT)):
                if every == 2:
                    jstart = (i - a * start) - (i - a * start) // every
                elif every == 1:
                    jstart = i - a * start
                else:
                    pass
                for j in range(max(0, jstart), n_samples):
                    if every == 2:
                        k = (i - a * start) % 2 + (j - jstart) * every
                    elif every == 1:
                        k = j - jstart
                    else:
                        pass
                    if k < K:
                        # NumPy uses row-major format
                        for b in range(batch_size):
                            for f in range(F):
                                y[i, b] += filters[k, f] * x[j, b]
        return y

    return _numba_mm(x, filters)


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
