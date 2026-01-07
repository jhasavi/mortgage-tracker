import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

logger = logging.getLogger("mortgage_tracker.supabase")


class SupabaseWriter:
    def __init__(self, url: str, service_key: str):
        self.client: Client = create_client(url, service_key)

    def create_run(self, status: str = "started") -> int:
        data = {"status": status}
        res = self.client.table("runs").insert(data).execute()
        run_id = res.data[0]["id"]
        logger.info("run_created", extra={"run_id": run_id})
        return run_id

    def finish_run(self, run_id: int, status: str, stats: Optional[Dict[str, Any]] = None, error_text: Optional[str] = None) -> None:
        update = {
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "stats_json": stats or {},
            "error_text": error_text,
        }
        self.client.table("runs").update(update).eq("id", run_id).execute()
        logger.info("run_finished", extra={"run_id": run_id, "status": status})

    def upsert_source(self, src: Dict[str, Any]) -> int:
        # Insert or ensure exists by name
        res = self.client.table("sources").upsert({
            "name": src.get("name"),
            "org_type": src.get("org_type"),
            "homepage_url": src.get("homepage_url"),
            "rate_url": src.get("rate_url"),
            "method": src.get("method"),
            "enabled": bool(src.get("enabled", True)),
            "notes": src.get("notes"),
        }, on_conflict="name").execute()
        return res.data[0]["id"]

    def insert_snapshot(self, snapshot: Dict[str, Any]) -> int:
        res = self.client.table("rate_snapshots").insert(snapshot).execute()
        return res.data[0]["id"]

    def insert_offers(self, offers: List[Dict[str, Any]]) -> None:
        if not offers:
            return
        self.client.table("offers_normalized").insert(offers).execute()
