"""Signal processing module."""

import warnings
from collections.abc import Callable, Iterable
from typing import Any

import numpy as np
from scipy import integrate, ndimage, optimize, signal


def _sanitize_dims_for_demodulation(
    reftime: np.ndarray, refsig: np.ndarray, sigtime: np.ndarray, sig: np.ndarray
):
    # Reference time vector should be 1D
    if reftime.ndim != 1:
        raise ValueError(
            "Reference time vector has too much dimensions, it should be 1D."
        )
    # Others should be 2D even with only one serie for vectorization
    if refsig.ndim == 1:
        refsig_na = refsig[..., np.newaxis]
    elif refsig.ndim == 2:
        refsig_na = refsig
    else:
        raise ValueError(
            "Reference signal has too much dimensions, it should be 1 or 2D."
        )
    if sigtime.ndim == 1:
        sigtime_na = sigtime[..., np.newaxis]
    elif (sigtime.ndim == 2) & (sigtime.shape[1] == 1):
        sigtime_na = sigtime
    else:
        raise ValueError(
            "Signal time vector has too much dimensions, it should be 1D "
            "or have its second dimension shape equal to 1."
        )
    if sig.ndim == 1:
        sig_na = sig[..., np.newaxis]
    elif sig.ndim == 2:
        sig_na = sig
    else:
        raise ValueError("Signal has too much dimensions, it should be 1 or 2D.")

    return reftime, refsig_na, sigtime_na, sig_na


def integrate_pickup(
    pickup_time: np.ndarray,
    pickup_signal: np.ndarray,
    pickup_surface: float,
    method: str = "trapz",
) -> np.ndarray:
    """
    Integrate pickup coil voltage to get the magnetic field.

    Uses Faraday-Lenz law : e = -SdB/dt. There could be multiple implementation to
    integrate, but only the cumulative trapezoid is implemented. The field is forced to
    be positive and starts at 0T.

    Parameters
    ----------
    pickup_time : np.ndarray
        1D vector with time points.
    pickup_signal : np.ndarray
        1D vector with pickup coil signal.
    pickup_surface : float
        Pickup coil surface in m².
    method : str, optional
        Method for the integration, by default "trapz".

    Returns
    -------
    magfield : np.ndarray
        Magnetic field in T.

    Raises
    ------
    ValueError
        Only 'trapz' is supported as integration `method`.

    """
    # Remove overall mean (offset) so that B is 0 when there's no magnetic field
    pu_signal = pickup_signal - np.mean(pickup_signal)

    # Integrate to get the field
    match method:
        case "trapz":
            magfield = (
                integrate.cumulative_trapezoid(pu_signal, pickup_time, initial=0)
                / pickup_surface
            )
        case _:
            err_msg = (
                "Only cumulative trapezoid integration method ('trapz') is implemented."
            )
            raise NotImplementedError(err_msg)

    # Fix inverted field
    if np.mean(magfield) < 0:
        magfield = -magfield

    return magfield


def rolling_average(
    a: np.ndarray, wlen: int, subsample: bool = False, axis=0
) -> np.ndarray:
    """
    Apply a rolling window average.

    The moving window is  applied on columns (with `axis=0`) or lines (with `axis=1`)
    of the input 2D array `a`. Optionally subsample the output.

    Parameters
    ----------
    a : np.ndarray
        2D array with series to smooth.
    wlen : int
        Time window size (expressed as indices).
    subsample : bool, optional
        If True, the series are sub-sampled `wlen - 1` times.
    axis : int, optional
        Direction to consider for time series, eg. 0 if time series to smooth are on the
        columns, 1 on lines. Default is 0.

    Returns
    -------
    smoothed_a : np.ndarray
        Array with smoothed time series.
    """
    # rolling average filter
    b = ndimage.uniform_filter1d(a, size=wlen, axis=axis, mode="reflect", origin=0)

    # subsampling, handling axes
    if subsample:
        b = subsample_array(b, wlen - 1, axis=axis)

    return b


def subsample_array(a: np.ndarray, step: int, axis: int = 0) -> np.ndarray:
    """
    Subsample an array in the given `axis` every `step` point.

    Parameters
    ----------
    a : np.ndarray
        Input array.
    step : int
        step::step points will be kept.
    axis : int < 2, optional
        Axis along which to operate, only 0 and 1 are supported. Default is 0 (along
        columns).

    Returns
    -------
    np.ndarray
        Subsampled array.

    Raises
    ------
    NotImplementedError
        If axis > 1.
    """
    if axis == 0:
        if a.ndim < 2:
            a = a[step::step].copy()
        else:
            a = a[step::step, :].copy()
    elif axis == 1:
        a = a[:, step::step].copy()
    else:
        raise NotImplementedError("Subsampling is not supported for axis > 1.")

    return a


def demodulate_chunks(
    reftime: np.ndarray,
    refsig: np.ndarray,
    sigtime: np.ndarray,
    sig: np.ndarray,
    f0: float,
    filter_order: int,
    filter_fc: float,
    decimate_factor: int = 0,
    chunksize: int = 0,
    bar: Callable[[Iterable], Iterable] | None = None,
    progress_emitter: Any = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Demodulation with IQ real signals.

    Reference signal is fitted to get its amplitude and phase over time. Those are used
    to generate a continuous reference signal, used to demodulate `signal`. The I and Q
    components are returned.

    The signal is frequency shifted with the continuous reference and a low-pass filter
    is applied.

    The process is done in chunks to not overload the memory, calling the `demodulate()`
    function on each chunk.

    Optionally, decimation can be used to reduce the data before filtering.

    Parameters
    ----------
    reftime : np.ndarray
        Time vector of the reference signal.
    refsig : np.ndarray
        2D array of the reference signal, cropped around where the fit will be done,
        time series should be on columns.
    sigtime : np.ndarray
        Time vector of the whole signal.
    sig : np.ndarray
        2D array representing the signal. Time series should be on columns.
    f0 : float
        Center frequency (experimental RF frequency).
    filter_order : int
        Order of the low-pass filter.
    filter_fc : float
        Cut-off frequency of the low-pass filter.
    decimate_factor : int, optional
        Downsampling factor, set to 0 or 1 to disable (default). An anti-aliasing filter
        is applied before.
    chunksize : int, optional
        Size of chunks, set to -1 to disable or 0 to adapt chunk size so that there are
        100 chunks (default).
    bar : Callable or None, optional
        Decorator for the main loop. Should be a callable that takes an iterable as
        argument to display a progress bar. Tested for `rich.progress.track()` and
        `tqdm.tqdm()`). Default is None (no progress bar).
    progress_emitter : Any or None, optional
        An object with an `emit()` method, such as a pyqtSignal. The loop index (e.g.
        frames index) is emitted at each iteration of the main loop. Default is None.

    Returns
    -------
    I, Q : np.ndarray
        I-Q-Demodulated signal.
    """
    # Dimensions checks
    reftime, refsig, sigtime, sig = _sanitize_dims_for_demodulation(
        reftime, refsig, sigtime, sig
    )

    npoints, nframes = sig.shape
    if decimate_factor > 1:
        new_npoints = int(npoints / decimate_factor)
        new_shape = (new_npoints, nframes)
    else:
        new_shape = (npoints, nframes)

    # Find reference phase
    def cos_func(
        x: np.ndarray, A: float | np.ndarray, phi: float | np.ndarray
    ) -> np.ndarray:
        return A * np.cos(2 * np.pi * f0 * x + phi)

    # Initialize output arrays
    X = np.empty(new_shape, float)
    Y = np.empty(new_shape, float)

    # Design low-pass filter
    fs = 1 / np.mean(np.diff(sigtime, axis=0))
    if decimate_factor > 1:
        fs = fs / decimate_factor
    sos = signal.butter(filter_order, filter_fc, btype="lowpass", fs=fs, output="sos")

    # Determine chunk size
    chunks, cs = get_chunks(nframes, chunksize)

    if bar is not None:
        chunks = bar(chunks)

    # Processing in chunks
    for idx in chunks:
        # Select data
        s = slice(idx, idx + cs + 1)
        refsig_chunk = refsig[:, s]
        sig_chunk = sig[:, s]

        X[:, s], Y[:, s] = demodulate(
            reftime,
            refsig_chunk,
            sigtime,
            sig_chunk,
            cos_func,
            sos,
            decimate_factor=decimate_factor,
        )

        if progress_emitter is not None:
            progress_emitter.emit(idx)

    return X, Y


def demodulate(
    reftime: np.ndarray,
    refsig: np.ndarray,
    sigtime: np.ndarray,
    sig: np.ndarray,
    func: Callable[[np.ndarray, float | np.ndarray, float | np.ndarray], np.ndarray],
    sos: np.ndarray,
    decimate_factor: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Classical demodulation with IQ real signals.

    Reference signal is fitted to get amplitude and phase. Those are used to generate
    a continuous reference signal, used to demodulate `signal`. The I and Q components
    are returned.

    The signal is frequency shifted with the continuous reference and a low-pass filter
    is applied. The process is done in chunks to not overload the memory.

    Optionally, decimation can be used to reduce the data before filtering. In that
    case, the filter second-order sections `sos` must take into account the reduced
    sampling frequency.

    Parameters
    ----------
    reftime : np.ndarray
        Time vector of the reference signal.
    refsig : np.ndarray
        2D array of the reference signal, cropped around where the fit will be done,
        time series should be on columns.
    sigtime : np.ndarray
        Time vector of the whole signal.
    sig : np.ndarray
        2D array representing the signal. Time series should be on columns.
    func : Callable
        Function taking a vector and 2 constants as arguments and returns a vector the
        same size as input. It is used to fit the reference so it should be a cosine
        function where the amplitude and the phase are fitted -- center frequency f0
        should be within the function.
    sos : np.ndarray
        Second-order sections representation of the IIR filter, as returned by
        `scipy.signal` filters. It must take into account the decimation.
    decimate_factor : int, optional
        Downsampling factor, set to 0 to disable (default). An anti-aliasing filter is
        applied before.

    Returns
    -------
    I, Q : np.ndarray
        I-Q-Demodulated signal.
    """
    # Dimensions checks
    reftime, refsig, sigtime, sig = _sanitize_dims_for_demodulation(
        reftime, refsig, sigtime, sig
    )

    # Fitting
    refas = np.empty((refsig.shape[1],), dtype=float)
    refphis = np.empty((refsig.shape[1],), dtype=float)
    for frame in range(refsig.shape[1]):
        popt, _ = optimize.curve_fit(func, reftime, refsig[:, frame])
        refas[frame] = popt[0]  # reference amplitude
        refphis[frame] = popt[1]  # reference phase

    # Multiply signal by reference (frequency-shifting)
    x = func(sigtime, refas, refphis) * sig
    y = func(sigtime, refas, refphis + np.pi / 2) * sig

    # Decimation (subsampling with anti-aliasing)
    if decimate_factor > 1:
        x = signal.decimate(x, decimate_factor, axis=0)
        y = signal.decimate(y, decimate_factor, axis=0)
    else:
        x = x
        y = y

    # Low-pass filter
    x = signal.sosfiltfilt(sos, x, axis=0)
    y = signal.sosfiltfilt(sos, y, axis=0)

    return x, y


def find_signal(
    sig: np.ndarray, std_factor: float, before: float = 0, after: float = 0
) -> tuple[int, int]:
    """
    Detect onset and offset of signal.

    Signal is defined as when the values are above/below the mean +/- `std_factor` times
    the standard deviation of the whole trace. Onset (offset) are the first (last, resp.)
    indices where this condition is met.
    `sig` can be 2D, in which case time series should be on column. The minimum index is
    selected for the onset and the last for offset.

    Parameters
    ----------
    sig : np.ndarray
        Array with time series on columns.
    std_factor : float
        Multipler of signal standard deviation.
    before : float, optional
        Fraction to take before the actual detected onset, by default 0.
    after : float, optional
        Fraction to take after the actual detected onset, by default 0.

    Returns
    -------
    start, stop : int
        Indices of onset and offset.
    """
    npoints = sig.shape[0]

    # Convert to float instead of doing it twice (mean and std)
    findsig = sig.astype(float)

    # Get threshold
    thresh = np.abs(findsig.mean(axis=0)) + std_factor * findsig.std(axis=0)

    # Binary mask
    mask = np.abs(findsig) > thresh

    # Find first non-zero value
    first = mask.argmax(axis=0).min()
    last = npoints - np.flip(mask, axis=0).argmax(axis=0).min()

    # Take a bit more or less
    delta = last - first
    first -= before * delta  # x% before onset
    last += after * delta  # x% after offset
    # Check boundaries
    first = max(0, int(first))
    last = min(int(last), npoints)
    # Check they didn't reverse, otherwise swap the two
    if last < first:
        ffirst = last
        last = first
        first = ffirst

    return first, last


def find_f0(sig: np.ndarray, fs: float) -> np.ndarray:
    """
    Find center frequency in signal `sig` sampled at `fs`.

    `sig` can be 2D, in which case the time series should be on columns, and the mean
    frequency found in each time series is returned.

    It uses the gaussian spectrum interpolation method described in Gasior & Gonzalez
    (2004) (1).

    (1) M. Gasior and J.L. Gonzalez, Improving FFT Frequency Measurement Resolution by
    Parabolic and Gaussian Spectrum Interpolation, CERN, 2004.

    Parameters
    ----------
    sig : np.ndarray
        S
    fs : float
        Sampling rate.

    Returns
    -------
    f0 : float
        Center frequency in same units as `fs`, one value per serie (columns of `sig`).
    """
    serie = sig.copy()
    npoints = serie.shape[0]

    # Check dimensions for compatibility with multiple time series
    if serie.ndim == 1:
        serie = serie[..., np.newaxis]

    # Indices vector
    time_ind = np.arange(npoints)[..., np.newaxis]

    # Gaussian coef.
    t0 = (time_ind[0, :] + time_ind[-1, :]) * 0.5
    c = 0.5 * (8 / (npoints - 1)) ** 2  # gaussian interp. with r=8
    gaussian = np.exp(-((time_ind - t0) ** 2) * c)

    # RFFT
    Sn = np.abs(np.fft.rfft(serie * gaussian, axis=0))
    f = np.fft.rfftfreq(npoints, d=1 / fs)

    # Frequency at FFT peak
    amax = Sn.argmax(axis=0)
    if np.all(0 < amax) & np.all(amax < f.shape[0]):
        indexer = np.arange(len(amax))
        dm = (
            fs
            / npoints
            * np.log(Sn[amax + 1, indexer] / Sn[amax - 1, indexer])
            / (
                2
                * np.log(
                    Sn[amax, indexer] ** 2
                    / (Sn[amax + 1, indexer] * Sn[amax - 1, indexer])
                )
            )
        )
        f0 = f[amax] + dm
    else:
        # Too close to the boundaries of the FFT window
        warnings.warn(
            "Center frequency is at the boundary of the window, "
            "can't interpolate properly."
        )
        f0 = f[amax]

    return f0


def compute_amp_iq(in_phase: np.ndarray, out_phase: np.ndarray) -> np.ndarray:
    """
    Compute amplitude from I and Q.

    Parameters
    ----------
    in_phase, out_phase : np.ndarray
        Same sized arrays corresponding to I and Q respectively.

    Returns
    -------
    amplitude : np.ndarray
        Signal amplitude.
    """
    return np.sqrt(in_phase**2 + out_phase**2)


def compute_phase_iq(
    in_phase: np.ndarray,
    out_phase: np.ndarray,
    unwrap: bool = False,
    period: float = np.pi,
    axis: int = 1,
) -> np.ndarray:
    """
    Compute phase from I and Q.

    The result can be unwrapped, in which case an axis must be specified.

    Parameters
    ----------
    in_phase, out_phase : np.ndarray
        Same sized arrays corresponding to I and Q respectively.
    unwrap : bool, optional
        Unwrap resulting phase. Default is False.
    period : float, optional
        Period considered for unwrapping, used only if `unwrap` is True. Default is pi.
    axis : int
        If `unwrap` is True, defines in which axis are time series, default is 1 (time
        series on columns).

    Returns
    -------
    phase : np.ndarray
        Signal phase.
    """
    res = np.arctan2(out_phase, in_phase)

    if unwrap:
        res = np.unwrap(res, period=period, axis=axis)

    return res


def rescale_a2b(
    a: np.ndarray, b: np.ndarray, allow_offset: bool = False, sub_mean: bool = False
) -> np.ndarray:
    """
    Rescale `a` so that it is in the same range as `b`.

    If `allow_offset` is False (default), the minimum will be set at 0 instead. If
    `sub_mean` is True, the mean is subtracted from the final array before returning.

    Parameters
    ----------
    a : np.ndarray
        Array to rescale.
    b : np.ndarray
        Array to get range from.
    allow_offset : bool, optionnal
        If False (default), the minimum value of the returned array is 0, otherwise, it
        is the minimum of `b`.
    sub_mean : bool, optionnal
        If True, the mean is subtracted from the rescaled array. Default is False.

    Returns
    -------
    rescaled_a : np.ndarray
        `a`, rescaled.

    """
    acopy = a.copy().astype(float)
    amin, amax = acopy.min(), acopy.max()
    bmin, bmax = b.min().astype(float), b.max().astype(float)
    rescaled_a = ((acopy - amin) / (amax - amin)) * (bmax - bmin)
    if allow_offset:
        rescaled_a += bmin
    if sub_mean:
        rescaled_a -= rescaled_a.mean()

    return rescaled_a


def get_chunks(nitems, chunk_size) -> tuple[range, int]:
    """
    Get a range generator.

    The generator goes from 0 to `nitems` with steps of `chunk_size`.
    If `chunk_size` is -1, it goes from 0 to `nitems` in one step (i.e. no chunking).
    If `chunk_size` is 0, it adjusts the step size to get 100 chunks.

    Parameters
    ----------
    nitems : int
        Total number of items.
    chunk_size : int
        Step size. -1 and 0 are treated as special values (see description above).

    Returns
    -------
    range : range
        Range generator.
    step_size : int
        The step size (chunk size) that was determined.
    """
    # Determine chunk size
    if chunk_size == -1:
        # no chunking
        cs = nitems
    elif chunk_size == 0:
        # get 100 chunks
        cs = nitems // 100
    else:
        cs = chunk_size

    return range(0, nitems, cs), cs


def compute_attenuation(
    amp: np.ndarray,
    amp0: float,
    echo_idx: int,
    length: float,
    mode: str = "reflection",
    corr: float = 1,
) -> np.ndarray:
    """
    Compute the normalized amplitude : attenuation in dB/m.

    Parameters
    ----------
    amp : np.ndarray
        Amplitude time serie.
    amp0 : float
        Amplitude baseline.
    echo_idx : int
        Index of the analyzed echo (1-based).
    length : float
        Sample length in m.
    mode : {"reflection" , "transmission"}, optional
        Detection mode, by default "reflection".
    corr : float, optional
        Denominator correction factor (logarithmic amplificator slope). Default is 1
        (no correction).

    Returns
    -------
    attenuation : np.ndarray
        Normalized amplitude in dB/m.

    """
    match mode:
        case "reflection":
            # reflection : 2nL
            constant = 2 * echo_idx

        case "transmission":
            # transmission : (2n - 1)L
            constant = 2 * echo_idx - 1

        case _:
            raise ValueError(
                "Expected 'reflection' or 'transmission' for detection mode. "
                f"Got {mode}."
            )

    return (amp0 - amp) / (corr * constant * length)


def compute_phase_shift(
    phi: np.ndarray,
    phi0: float,
    echo_idx: int,
    speed: float,
    rf_freq: float,
    length: float,
    mode: str = "reflection",
) -> np.ndarray:
    """
    Compute relative phase-shift.

    Parameters
    ----------
    phi : np.ndarray
        Pi-jump-corrected phase time serie.
    phi0 : float
        Phase baseline.
    echo_idx : int
        Index of analyzed echo (1-based).
    speed : float
        (Estimated) speed of sound in the sample.
    rf_freq : float
        Radiofrequency frequency used in the experiment in Hz.
    length : float
        Sample length in m.
    mode : {"reflection", "transmission"}, optional
        Detection mode, by default "reflection".

    Returns
    -------
    deltaphi : np.ndarray
        Relative phase-shift.

    """
    match mode:
        case "reflection":
            # reflection : 2nL
            constant = 2 * echo_idx
        case "transmission":
            # transmission (2n - 1)L
            constant = 2 * echo_idx - 1
        case _:
            raise ValueError(
                "Expected 'reflection' or 'transmission' for detection mode. "
                f"Got {mode}."
            )

    return (phi - phi0) * speed / (2 * np.pi * rf_freq * constant * length)
