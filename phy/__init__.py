"""5G NR PHY building blocks for the software-in-the-loop prototype."""

from .artifacts import normalize_pipeline_stage, normalize_stage_artifact, pipeline_stage, stage_artifact
from .context import SlotContext
from .kpi import LinkKpiSummary
from .modulation import ModulationMapper
from .numerology import NumerologyConfig
from .receiver import NrReceiver, RxResult
from .transmitter import NrTransmitter, TxResult
from .types import SpatialLayout, TensorViewSpec

__all__ = [
    "LinkKpiSummary",
    "ModulationMapper",
    "NumerologyConfig",
    "NrReceiver",
    "NrTransmitter",
    "RxResult",
    "SlotContext",
    "SpatialLayout",
    "TensorViewSpec",
    "TxResult",
    "normalize_pipeline_stage",
    "normalize_stage_artifact",
    "pipeline_stage",
    "stage_artifact",
]
