from __future__ import annotations

import numpy as np

try:  # pragma: no cover - depends on GNU Radio runtime
    from gnuradio import blocks, channels, filter, gr

    HAVE_GNURADIO = True
except ImportError:  # pragma: no cover
    HAVE_GNURADIO = False


class EndToEndFlowgraph:
    """GNU Radio loopback used as an optional channel wrapper around the Python PHY."""

    def __init__(
        self,
        waveform: np.ndarray,
        sample_rate: float,
        noise_variance: float,
        frequency_offset_hz: float,
        taps: np.ndarray | None = None,
    ) -> None:
        if not HAVE_GNURADIO:
            raise RuntimeError("GNU Radio is not installed in this environment.")

        taps = np.asarray(taps if taps is not None else np.array([1.0 + 0j]), dtype=np.complex64)
        self.tb = gr.top_block("nr_end_to_end_flowgraph")
        self.source = blocks.vector_source_c(waveform.astype(np.complex64).tolist(), False, 1, [])
        self.throttle = blocks.throttle(gr.sizeof_gr_complex, sample_rate, True)
        self.fir = filter.fir_filter_ccc(1, taps.tolist())
        self.channel = channels.channel_model(
            noise_voltage=float(np.sqrt(noise_variance / 2.0)),
            frequency_offset=float(frequency_offset_hz / sample_rate),
            epsilon=1.0,
            taps=[1.0 + 0j],
            noise_seed=0,
            block_tags=False,
        )
        self.sink = blocks.vector_sink_c()
        self.tb.connect(self.source, self.throttle)
        self.tb.connect(self.throttle, self.fir)
        self.tb.connect(self.fir, self.channel)
        self.tb.connect(self.channel, self.sink)

    def run_and_collect(self) -> np.ndarray:
        self.tb.run()
        return np.asarray(self.sink.data(), dtype=np.complex64)
