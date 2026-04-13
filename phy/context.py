from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class SlotContext:
    timeline_index: int
    frame_index: int
    slot_index: int
    slots_per_frame: int

    @property
    def slot_label(self) -> str:
        return f"Frame {self.frame_index} / Slot {self.slot_index}"

    def as_dict(self) -> dict[str, int | str]:
        return {
            "timeline_index": int(self.timeline_index),
            "frame_index": int(self.frame_index),
            "slot_index": int(self.slot_index),
            "slots_per_frame": int(self.slots_per_frame),
            "slot_label": self.slot_label,
        }
