"""Utilities allowing to use streams for chunked data analysis

The `DataAnalyser` class allows performing various data analysis tasks on arbitrary
sets of streams. Currently, it provides a Welch PSD estimator as well as minimum, maximum,
and mean. The results are collected in a dataclass DataAnalyserResults. Further, it can
check for occurrence of NANs and INFs.
"""

from dataclasses import dataclass, field
from typing import Any, Final, Literal, Protocol

import numpy as np
import scipy

from lisainstrument.streams.expression import stream_expression
from lisainstrument.streams.null_store import DataStorageDiscard
from lisainstrument.streams.scheduler import (
    SchedulerConfigSerial,
    SchedulerConfigTypes,
    store_bundle,
)
from lisainstrument.streams.segments import Segment, SegmentConst, segment_empty
from lisainstrument.streams.streams import (
    DatasetIdentifier,
    StreamBase,
    StreamBundle,
    StreamConst,
    StreamDependency,
)


class Accumulator(Protocol):
    """Protocol for classes accumulating data from chunked data"""

    def __call__(self, chunk: np.ndarray) -> None:
        """Process another strech of data"""

    @property
    def result(self):
        """Latest result"""

    @property
    def dtype(self):
        """input data type"""


class AccumulatorMax(Accumulator):
    """Gather maximum value from chunked data"""

    def __init__(self, dtype):
        self._result = None
        self._dtype = np.dtype(dtype)

    def __call__(self, chunk: np.ndarray) -> None:
        """Process another strech of data"""
        chres = np.max(chunk).tolist()
        self._result = chres if self._result is None else max(self._result, chres)

    @property
    def result(self):
        """Latest result"""
        return self._result

    @property
    def dtype(self):
        """input data type"""
        return self._dtype


class AccumulatorMin(Accumulator):
    """Gather minimum value from chunked data"""

    def __init__(self, dtype):
        self._result = None
        self._dtype = np.dtype(dtype)

    def __call__(self, chunk: np.ndarray) -> None:
        """Process another strech of data"""
        chres = np.min(chunk).tolist()
        self._result = chres if self._result is None else min(self._result, chres)

    @property
    def result(self):
        """Latest result"""
        return self._result

    @property
    def dtype(self):
        """input data type"""
        return self._dtype


@dataclass
class PSDEstimate:
    """Store results of PSD estimation.

    This represents estimated one-sided PSDs of real-valued time series.

    Attributes:
        freq: Array with centers of frequency bins
        psd: One-sided PSD
    """

    freq: np.ndarray
    psd: np.ndarray


class AccumulatorWelchPSD(Accumulator):
    """Gather Welch PSD estimate from chunked data"""

    def __init__(
        self,
        seg_length: int,
        seg_over: int,
        dt: float,
        window=None,
        detrend: bool | str = False,
    ):
        self._seg_len: Final = int(seg_length)
        self._shift: Final = self._seg_len - int(seg_over)
        self._dt: Final = float(dt)

        if self._seg_len < 2:
            msg = f"AccumulatorWelchPSD: got seg_length {seg_length}, must be >=2"
            raise ValueError(msg)
        if not 0 <= seg_over < seg_length:
            msg = f"AccumulatorWelchPSD: got invalid seg_over {seg_over} (with {seg_length=})"
            raise ValueError(msg)
        if self._dt <= 0 or not np.isfinite(self._dt):
            msg = f"AccumulatorWelchPSD: got invalid {dt=}"
            raise ValueError(msg)

        match window:
            case None:
                _win = scipy.signal.get_window("hann", self._seg_len)
            case str() | tuple() as named:
                _win = scipy.signal.get_window(named, self._seg_len)
            case list() | np.ndarray() as coeffs:
                if len(coeffs) != seg_length:
                    msg = "AccumulatorWelchPSD: Window length does not match segment length"
                    raise RuntimeError(msg)
                _win = np.ndarray(coeffs)
            case _:
                msg = f"AccumulatorWelchPSD: window parameter must be None|str|list|numpy.ndarray, got {type(window)}"
                raise TypeError(msg)
        self._win: Final = _win / np.sqrt(np.sum(_win**2))

        self._detrend: Final = detrend

        # non-negative frequency portion of two-sided DFT
        self._psd = np.zeros(self._seg_len // 2 + 1, dtype=self.dtype)
        self._npsds = 0
        self._buf = np.zeros(self._seg_len, dtype=self.dtype)
        self._inext = 0

    def _get_psd(self, seg):
        """Get PSD from detrended windowed data segment"""
        match self._detrend:
            case False:
                _y = seg
            case str(named):
                _y = scipy.signal.detrend(seg, type=named)
            case _:
                msg = f"AccumulatorWelchPSD: invalid detrend parameter {self._detrend}"
                raise RuntimeError(msg)

        return np.abs(np.fft.rfft(_y * self._win)) ** 2

    def __call__(self, chunk: np.ndarray) -> None:
        """Process another strech of data"""
        if chunk.dtype != self.dtype:
            msg = f"AccumulatorWelchPSD requires data of type {self.dtype} got {chunk.dtype}"
            raise TypeError(msg)

        ichnk = 0
        while ichnk < len(chunk):
            nadv = min(len(chunk) - ichnk, self._seg_len - self._inext)
            self._buf[self._inext : self._inext + nadv] = chunk[ichnk : ichnk + nadv]
            self._inext += nadv
            ichnk += nadv

            if self._inext == self._seg_len:
                self._psd += self._get_psd(self._buf)
                self._npsds += 1
                self._buf[: -self._shift] = self._buf[self._shift :]
                self._inext -= self._shift

    @property
    def result(self):
        """Latest result"""
        twosided_to_onesided = 2.0
        psd_onesided = self._psd * (twosided_to_onesided * self._dt / self._npsds)
        psd_onesided[0] /= twosided_to_onesided
        if self._seg_len % 2 == 0:  # last element is at f_nyquist
            psd_onesided[-1] /= twosided_to_onesided
        freq = np.fft.rfftfreq(self._seg_len, d=self._dt)
        return PSDEstimate(freq=freq, psd=psd_onesided)

    @property
    def dtype(self):
        """input data type"""
        return np.float64


class StreamAccumulate(StreamBase):
    """Analysis Stream calling accumulator object with consecutive chunks.

    The output of this stream is zero. The whole purpose of this stream lies in its
    side effect of passing the data to the accumulator.
    The accumulator is called with chunks in order in a serial fashion, and thus
    does not need to be thread-safe.
    """

    def __init__(self, refstream: StreamBase, accumulate: Accumulator):
        dep = StreamDependency(stream=refstream)
        super().__init__([dep], True, accumulate.dtype)
        self._acc: Final = accumulate

    def generate(
        self, state: Any, deps: list[Segment], istart: int, istop: int
    ) -> tuple[Segment, Any]:
        """Generate segment, see StreamBase documentation"""
        (seg,) = deps

        if not seg.istart <= istart <= istop <= seg.istop:
            msg = (
                f"StreamAccumulate: cannot process requested range [{istart}, {istop})"
            )
            raise RuntimeError(msg)

        if istart == istop:
            return segment_empty(istart, self.dtype), True

        dat = np.empty(istop - istart, dtype=self.dtype)
        seg.write(dat, istart=istart, istop=istop)

        self._acc(dat)

        dummy = SegmentConst(0.0, istart, istop - istart)
        return dummy, True


@dataclass
class DataAnalyserResults:
    """Collects result of DataAnalyser

    Attributes:
        max: Dictionary mappping dataset identifiers to dataset maximum value
        min: Dictionary mappping dataset identifiers to dataset minimum value
        psd: Dictionary mappping dataset identifiers to dataset PSD estimate
    """

    max: dict[DatasetIdentifier, Any] = field(default_factory=dict)
    min: dict[DatasetIdentifier, Any] = field(default_factory=dict)
    psd: dict[DatasetIdentifier, Any] = field(default_factory=dict)


@dataclass
class _ResultConstShortcut:
    result: Any


class DataAnalyser:
    """Collect streams data analysis tasks and execute them

    Instance of this is used by passing streams to methods representing
    data analysis tasks, such as PSD estimator. The analysis is not performed
    immediately, but when the `compute` method is called. The analysis is executed
    in a memory and CPU efficient way. Each stream is evaluated only once. If the
    dependency graph of the analysis has disconnected components, they are processed
    one after the other. Collecting all analysis tasks in one big DataAnalyser
    collection is therefore still memory efficient.

    When adding an analysis tasks, one has to provide the index range over which
    the stream is to be evaluated. Since streams are potentially infinite, they do
    not have a range attached. However, the main use case of this method is to
    analyse streams representing datasets in instrument file reader results. Such
    streams as well as the available index ranges can be obtained from a
    `SimResultFile` instance.

    The results returned by the `compute` method are given as a `DataAnalyserResults`
    instance, which stores the extracted stream data properties in dictionaries
    keyed by a `DatasetIdentifier` (a tuple of strings) that consists of a
    `DatasetIdentifier` for the stream provided by the user.
    """

    def _reset(self) -> None:
        self._stb = StreamBundle()
        self._max: dict[DatasetIdentifier, Any] = {}
        self._min: dict[DatasetIdentifier, Any] = {}
        self._psd: dict[DatasetIdentifier, Any] = {}

    def __init__(self) -> None:
        self._reset()

    def require_finite(
        self, stream: StreamBase, srange: tuple[int, int], dsid: DatasetIdentifier
    ) -> None:
        """Make sure stream data is finite, raise ValueError otherwise"""

        def canary(y):
            if not np.all(np.isfinite(y)):
                msg = f"Dataset {dsid} not finite"
                raise ValueError(msg)
            return 1.0

        if isinstance(stream, StreamConst):
            canary(stream.const)
        else:
            sfin = stream_expression(np.float64)(canary)(stream)
            self._stb.add((*dsid, "finite"), sfin, srange)

    def max(
        self, stream: StreamBase, srange: tuple[int, int], dsid: DatasetIdentifier
    ) -> None:
        """Gather maximum of stream data

        Arguments:
            stream: The stream to be analysed
            srange: Index range to analyse
            dsid: DatasetIdentifier used in DataAnalyserResults to refer to result
        """

        if isinstance(stream, StreamConst):
            self._max[dsid] = _ResultConstShortcut(result=stream.const)
        else:
            accu = AccumulatorMax(dtype=stream.dtype)
            self._max[dsid] = accu
            sacc = StreamAccumulate(stream, accu)
            self._stb.add((*dsid, "max"), sacc, srange)

    def min(
        self, stream: StreamBase, srange: tuple[int, int], dsid: DatasetIdentifier
    ) -> None:
        """Gather minimum of stream data

        Arguments:
            stream: The stream to be analysed
            srange: Index range to analyse
            dsid: DatasetIdentifier used in DataAnalyserResults to refer to result
        """
        if isinstance(stream, StreamConst):
            self._min[dsid] = _ResultConstShortcut(result=stream.const)
        else:
            accu = AccumulatorMin(dtype=stream.dtype)
            self._min[dsid] = accu
            sacc = StreamAccumulate(stream, accu)
            self._stb.add((*dsid, "min"), sacc, srange)

    def psd(
        self,
        stream: StreamBase,
        srange: tuple[int, int],
        dsid: DatasetIdentifier,
        *,
        seg_length: int,
        seg_over: int,
        dt: float,
        window=None,
        detrend: Literal[False] | str = False,
    ) -> None:
        """Gather Welch PSD estimate of stream data

        Arguments:
            stream: The stream to be analysed
            srange: Index range to analyse
            dsid: DatasetIdentifier used in DataAnalyserResults to refer to result
            seg_length: Number of samples for each Welch segment
            seg_over: Number of samples by which segments overlap
            dt: Sample period of the stream
            window: Name of window function, defaults to "hann"
            detrend: Detrend method 'linear', 'constant', or False for no detrending
        """

        accu = AccumulatorWelchPSD(
            seg_length=seg_length,
            seg_over=seg_over,
            dt=dt,
            window=window,
            detrend=detrend,
        )
        self._psd[dsid] = accu
        sacc = StreamAccumulate(stream, accu)
        self._stb.add((*dsid, "psd"), sacc, srange)

    def compute(
        self, config: SchedulerConfigTypes | None = None
    ) -> DataAnalyserResults:
        """Execute stored data analysis tasks and return results

        Internally, this creates special streams for each analysis task,
        then uses scheduler.store_bundle to evaluate them, but without
        actually storing the stream outputs anywhere. The data analysis is
        performed as a side effect of evaluating the streams.

        The upshot is that the same efficient machinery employed for performing
        simulations is used for the analysis and resource usage can be controlled
        in the same fashion, allowing multithreading and limiting memory use.

        Attributes:
            config: controls resource usage, see scheduler.store_bundle

        Returns:
            Results collected in DataAnalyserResults instance
        """

        discard = DataStorageDiscard(self._stb.output_ids)
        if config is None:
            config = SchedulerConfigSerial(chunk_size=100000)
        store_bundle(self._stb, discard, config)

        resmax = {dsid: a.result for dsid, a in self._max.items()}
        resmin = {dsid: a.result for dsid, a in self._min.items()}
        respsd = {dsid: a.result for dsid, a in self._psd.items()}

        self._reset()
        return DataAnalyserResults(max=resmax, min=resmin, psd=respsd)
