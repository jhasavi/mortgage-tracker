import logging
from typing import Optional

logger = logging.getLogger("mortgage_tracker.emailer")


def send_daily_summary(api_key: Optional[str], summary_text: str) -> None:
    # Optional stub: integrate with email provider (SendGrid, Postmark, etc.)
    if not api_key:
        logger.info("email_skipped_no_key")
        return
    # Implement provider integration here
    logger.info("email_sent_stub", extra={"length": len(summary_text)})
