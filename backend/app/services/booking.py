import functools
import random
from pathlib import Path

from openai import OpenAI

from app.config import settings
from app.schemas import BookingMode, BookingResult, BookingStatus


def get_client() -> OpenAI:
    return OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


@functools.lru_cache(maxsize=1)
def load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.txt"
    return prompt_path.read_text(encoding="utf-8")


def simulate_booking(
    mode: BookingMode,
    slot: str,
) -> BookingResult:
    """Simulate site visit booking with configurable success/fail."""
    if mode == BookingMode.RANDOM:
        success = random.choice([True, False])
    elif mode == BookingMode.FAIL:
        success = False
    else:
        success = True

    if success:
        return BookingResult(
            attempted=True,
            success=True,
            status=BookingStatus.CONFIRMED,
            message=f"Site visit confirmed for {slot}.",
            slot=slot,
        )

    return BookingResult(
        attempted=True,
        success=False,
        status=BookingStatus.FAILED,
        message=f"Could not confirm booking for {slot}. Slot may be unavailable.",
        slot=slot,
    )
