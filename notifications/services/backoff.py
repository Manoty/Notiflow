import logging

logger = logging.getLogger(__name__)


class ExponentialBackoff:
    """
    Calculates retry delay using exponential backoff with jitter.

    Why exponential?
    If 100 notifications fail simultaneously and all retry after exactly
    60 seconds, you create a thundering herd — 100 requests hit the
    SMTP server at once, which is exactly what caused the failure.
    Exponential backoff spreads retries over time.

    Why jitter?
    Even with exponential growth, multiple tasks started at the same time
    will retry at the same time. Adding a random ±20% jitter desynchronises
    them naturally.

    Default schedule:
        Attempt 1: ~60s   (1 minute)
        Attempt 2: ~300s  (5 minutes)
        Attempt 3: ~900s  (15 minutes)
    """

    BASE_DELAY    = 60      # seconds for the first retry
    MULTIPLIER    = 5       # each attempt multiplies the delay
    MAX_DELAY     = 3600    # cap at 1 hour regardless of attempt count
    JITTER_FACTOR = 0.2     # ±20% random variation

    @classmethod
    def delay_for_attempt(cls, attempt_number: int) -> int:
        """
        Returns the delay in seconds for a given retry attempt.
        attempt_number is 1-based (first retry = attempt 1).
        """
        import random

        raw_delay = cls.BASE_DELAY * (cls.MULTIPLIER ** (attempt_number - 1))
        capped    = min(raw_delay, cls.MAX_DELAY)

        # Apply jitter: ±JITTER_FACTOR of the capped delay
        jitter    = capped * cls.JITTER_FACTOR
        final     = int(capped + random.uniform(-jitter, jitter))

        logger.debug(
            f"Backoff: attempt={attempt_number} "
            f"raw={raw_delay}s capped={capped}s final={final}s"
        )
        return max(final, 10)   # never less than 10 seconds

    @classmethod
    def schedule(cls) -> list[int]:
        """Returns the full retry schedule for logging/display."""
        return [
            cls.delay_for_attempt(i)
            for i in range(1, 6)
        ]