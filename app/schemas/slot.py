from typing import Any


def slot_out(slot, available: bool) -> dict[str, Any]:
    return {
        "id": slot.id,
        "provider": slot.provider,
        "start": slot.start,
        "end": slot.end,
        "available": available,
    }
