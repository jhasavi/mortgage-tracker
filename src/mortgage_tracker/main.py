import json
import logging
import os
from datetime import datetime

from .config import load_config
from .fetch import fetch_url
from .normalize import normalize_offers
from .supabase_client import SupabaseWriter

# Configure basic structured logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("mortgage_tracker.main")


def _get_parser(method: str):
    if method == "example_html_table":
        from .parsers.example_html_table import ExampleHtmlTableParser
        return ExampleHtmlTableParser()
    if method == "example_json_endpoint":
        from .parsers.example_json_endpoint import ExampleJsonEndpointParser
        return ExampleJsonEndpointParser()
    if method == "dcu":
        from .parsers.dcu import DCUParser
        return DCUParser()
    raise ValueError(f"Unknown method: {method}")


def run_once():
    # Load config - use env var or default path in repo root
    sources_path = os.environ.get("SOURCES_YAML", "sources.yaml")
    if not os.path.isabs(sources_path):
        # Make it relative to cwd
        sources_path = os.path.abspath(sources_path)
    cfg = load_config(sources_path)
    sb = SupabaseWriter(cfg.supabase_url, cfg.supabase_service_role_key)
    run_id = sb.create_run(status="started")

    total_sources = 0
    success_sources = 0
    offers_written = 0

    for src in cfg.sources:
        total_sources += 1
        if not src.get("enabled", True):
            logger.info(json.dumps({"event":"source_skipped","name":src.get("name")}))
            continue
        name = src.get("name")
        method = src.get("method")
        rate_url = src.get("rate_url")

        try:
            source_id = sb.upsert_source(src)
            status, text, js = fetch_url(rate_url, timeout=10.0, retries=2)
            snapshot = {
                "run_id": run_id,
                "source_id": source_id,
                "http_status": status,
                "raw_text": text,
                "raw_json": js,
                "parse_status": None,
                "parse_error": None,
            }

            parser = _get_parser(method)
            raw_offers = parser.parse(text=text, js=js)

            if raw_offers:
                snapshot["parse_status"] = "parsed"
            else:
                snapshot["parse_status"] = "skipped"
            snap_id = sb.insert_snapshot(snapshot)

            normalized = normalize_offers(raw_offers, cfg.defaults)
            for n in normalized:
                n["run_id"] = run_id
                n["source_id"] = source_id
            if normalized:
                sb.insert_offers(normalized)
                offers_written += len(normalized)
                success_sources += 1
            logger.info(json.dumps({"event":"source_done","name":name,"offers":len(normalized),"snapshot_id":snap_id}))
        except Exception as e:
            logger.error(json.dumps({"event":"source_error","name":name,"error":str(e)}))
            try:
                # Best-effort snapshot insert with error
                source_id = sb.upsert_source(src)
                sb.insert_snapshot({
                    "run_id": run_id,
                    "source_id": source_id,
                    "http_status": 0,
                    "raw_text": None,
                    "raw_json": None,
                    "parse_status": "failed",
                    "parse_error": str(e),
                })
            except Exception:
                pass

    status = "success" if success_sources == total_sources else ("partial" if success_sources > 0 else "failed")
    stats = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_sources": total_sources,
        "success_sources": success_sources,
        "offers_written": offers_written,
    }
    sb.finish_run(run_id, status=status, stats=stats)
    logger.info(json.dumps({"event":"run_finished","run_id":run_id,"status":status,"stats":stats}))


if __name__ == "__main__":
    run_once()
