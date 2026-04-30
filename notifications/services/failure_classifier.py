import re
import logging

logger = logging.getLogger(__name__)


class FailureClassifier:
    """
    Determines whether a failed notification delivery should be retried.

    The rule is simple but important:
        Transient failures  → caused by temporary conditions → retry
        Permanent failures  → caused by bad data or config   → do not retry

    Retrying permanent failures wastes resources and can get your
    sending domain flagged as spam (repeated sends to invalid addresses).
    """

    # Error substrings that indicate a permanent failure.
    # Retrying these will never succeed.
    PERMANENT_ERROR_PATTERNS = [
        # SMTP / Email
        r'invalid\s+recipient',
        r'user\s+unknown',
        r'no\s+such\s+user',
        r'address\s+rejected',
        r'does\s+not\s+exist',
        r'bad\s+header',
        r'authentication\s+failed',       # wrong credentials — fix config, not retry
        r'smtpauthenticationerror',

        # SMS / Gateway
        r'invalidsenderid',
        r'invalid\s+phone',
        r'invalid\s+phone\s+format',
        r'cannot\s+resolve\s+phone',
        r'cannot\s+resolve\s+recipient',
        r'insufficientbalance',            # account balance — needs human action

        # Application-level
        r'no\s+service\s+registered',
        r'not\s+an\s+email\s+address',
    ]

    # Compiled once at class load — not on every call
    _PERMANENT_RE = [
        re.compile(p, re.IGNORECASE)
        for p in PERMANENT_ERROR_PATTERNS
    ]

    @classmethod
    def is_transient(cls, error_message: str | None) -> bool:
        """
        Returns True if the error looks transient (worth retrying).
        Returns False if it looks permanent (give up immediately).
        If error_message is None or empty, assume transient — something
        unexpected happened and a retry is worth attempting.
        """
        if not error_message:
            return True

        for pattern in cls._PERMANENT_RE:
            if pattern.search(error_message):
                logger.debug(
                    f"Classified as PERMANENT (matched '{pattern.pattern}'): "
                    f"{error_message[:120]}"
                )
                return False

        logger.debug(f"Classified as TRANSIENT: {error_message[:120]}")
        return True