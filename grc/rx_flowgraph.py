from __future__ import annotations

import numpy as np

try:  # pragma: no cover - depends on GNU Radio runtime
    from gnuradio import blocks, gr, qtgui
    from gnuradio.fft import window

    HAVE_GNURADIO = True
except ImportError:  # pragma: no cover
    HAVE_GNURADIO = False


class RxFlowgraph:
    """GNU Radio RX observation flowgraph for received IQ samples."""

    def __init__(self, waveform: np.ndarray, sample_rate: float) -> None:
        if not HAVE_GNURADIO:
            raise RuntimeError("GNU Radio is not installed in this environment.")
        self.tb = gr.top_block("nr_rx_flowgraph")
        self.source = blocks.vector_source_c(waveform.astype(np.complex64).tolist(), False, 1, [])
        self.throttle = blocks.throttle(gr.sizeof_gr_complex, sample_rate, True)
        self.time_sink = qtgui.time_sink_c(1024, sample_rate, "RX Waveform", 1)
        self.constellation_sink = qtgui.const_sink_c(1024, "RX Constellation", 1)
        self.freq_sink = qtgui.freq_sink_c(2048, window.WIN_BLACKMAN_hARRIS, 0, sample_rate, "RX Spectrum", 1)
        self.tb.connect(self.source, self.throttle)
        self.tb.connect(self.throttle, self.time_sink)
        self.tb.connect(self.throttle, self.constellation_sink)
        self.tb.connect(self.throttle, self.freq_sink)

    def start(self) -> None:
        self.tb.start()

    def wait(self) -> None:
        self.tb.wait()
