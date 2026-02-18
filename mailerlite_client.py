import logging
from typing import Any, Dict, Optional

import requests


logger = logging.getLogger(__name__)


class MailerLiteClassicClient:
    def __init__(self, api_key: str, base_url: str = "https://api.mailerlite.com/api/v2"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def add_subscriber_to_group(
        self,
        group_id: str,
        email: str,
        name: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        timeout_s: int = 15,
    ) -> bool:
        """Add (or upsert) a subscriber into a MailerLite Classic group.

        Classic endpoint:
          POST https://api.mailerlite.com/api/v2/groups/{id}/subscribers
        """

        if not self.api_key:
            logger.warning("MAILERLITE_API_KEY not set; skipping MailerLite group sync")
            return False
        if not group_id:
            logger.warning("MAILERLITE_GROUP_ID not set; skipping MailerLite group sync")
            return False
        if not email:
            return False

        payload: Dict[str, Any] = {"email": email}
        if name:
            payload["name"] = name
        if fields:
            payload["fields"] = fields

        headers = {
            "X-MailerLite-ApiKey": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/groups/{group_id}/subscribers"
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
        except requests.RequestException as e:
            logger.error(f"MailerLite request failed: {e}")
            return False

        # Classic usually returns 200 on success.
        if 200 <= resp.status_code < 300:
            return True

        # Don't raise; this runs in background threads.
        logger.warning(
            f"MailerLite add_subscriber_to_group failed: {resp.status_code} - {resp.text}"
        )
        return False


