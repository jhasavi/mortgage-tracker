"""
Main collector entry point with enhanced run management and parser registry.
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

from .config import load_config
from .fetch import fetch_url
from .normalize import normalize_offers
from .supabase_client import SupabaseWriter
from .parsers import get_parser

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("mortgage_tracker.main")


class CollectorStats:
    """Track statistics for a collector run."""
    
    def __init__(self):
        self.sources_total = 0
        self.sources_enabled = 0
        self.sources_success = 0
        self.sources_failed = 0
        self.sources_skipped = 0
        self.offers_inserted = 0
        self.parse_errors: List[Dict[str, str]] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sources_total": self.sources_total,
            "sources_enabled": self.sources_enabled,
            "sources_success": self.sources_success,
            "sources_failed": self.sources_failed,
            "sources_skipped": self.sources_skipped,
            "offers_inserted": self.offers_inserted,
            "parse_errors": self.parse_errors[:10],  # Limit to first 10 errors
        }


def run_collector(run_type: str = "real", sources_path: str = None) -> Dict[str, Any]:
    """
    Run the mortgage rate collector.
    
    Args:
        run_type: 'real' or 'sample' - determines how data is tagged
        sources_path: Path to sources.yaml file
        
    Returns:
        Dict with run_id, status, and stats
    """
    # Load configuration
    if sources_path is None:
        sources_path = os.environ.get("SOURCES_YAML", "sources.yaml")
    if not os.path.isabs(sources_path):
        sources_path = os.path.abspath(sources_path)
    
    logger.info(f"Starting collector run (type={run_type}, sources={sources_path})")
    
    cfg = load_config(sources_path)
    sb = SupabaseWriter(cfg.supabase_url, cfg.supabase_service_role_key)
    
    # Create run record
    run_id = sb.create_run(status="started", run_type=run_type)
    logger.info(f"Created run {run_id} (type={run_type})")
    
    stats = CollectorStats()
    
    # Process each source
    for src in cfg.sources:
        stats.sources_total += 1
        source_name = src.get("name", src.get("id", "unknown"))
        
        # Skip disabled sources
        if not src.get("enabled", False):
            stats.sources_skipped += 1
            logger.info(f"⏭️  Skipping disabled source: {source_name}")
            continue
        
        stats.sources_enabled += 1
        rate_url = src.get("rate_url") or src.get("url")
        parser_key = src.get("parser_key") or src.get("method")
        
        if not rate_url:
            logger.warning(f"⚠️  Source {source_name} has no rate_url, skipping")
            stats.sources_skipped += 1
            continue
        
        if not parser_key or parser_key == "none":
            logger.warning(f"⚠️  Source {source_name} has no parser_key, skipping")
            stats.sources_skipped += 1
            continue
        
        # Process this source
        try:
            logger.info(f"📥 Fetching {source_name} from {rate_url}")
            
            # Upsert source record
            source_id = sb.upsert_source(src)
            
            # Fetch content
            status_code, text, js = fetch_url(rate_url, timeout=15.0, retries=2)
            
            # Always store snapshot
            snapshot = {
                "run_id": run_id,
                "source_id": source_id,
                "http_status": status_code,
                "raw_text": text,
                "raw_json": js,
                "parse_status": None,
                "parse_error": None,
            }
            
            # Attempt to parse
            raw_offers = []
            parse_error = None
            
            try:
                parser = get_parser(parser_key)
                raw_offers = parser.parse(text=text, js=js)
                
                if raw_offers:
                    snapshot["parse_status"] = "success"
                    logger.info(f"✅ Parsed {len(raw_offers)} offers from {source_name}")
                else:
                    snapshot["parse_status"] = "empty"
                    logger.warning(f"⚠️  No offers parsed from {source_name}")
                    
            except KeyError as e:
                parse_error = f"Parser not found: {e}"
                snapshot["parse_status"] = "error"
                snapshot["parse_error"] = parse_error
                logger.error(f"❌ {source_name}: {parse_error}")
                stats.parse_errors.append({"source": source_name, "error": parse_error})
                
            except Exception as e:
                parse_error = str(e)
                snapshot["parse_status"] = "error"
                snapshot["parse_error"] = parse_error
                logger.error(f"❌ {source_name}: Parse error: {parse_error}")
                stats.parse_errors.append({"source": source_name, "error": parse_error})
            
            # Insert snapshot
            snap_id = sb.insert_snapshot(snapshot)
            
            # Normalize and insert offers
            if raw_offers:
                normalized = normalize_offers(raw_offers, cfg.defaults)
                
                for offer in normalized:
                    offer["run_id"] = run_id
                    offer["source_id"] = source_id
                    offer["data_source"] = "sample" if run_type == "sample" else "real"
                
                sb.insert_offers(normalized)
                stats.offers_inserted += len(normalized)
                stats.sources_success += 1
                
                logger.info(
                    f"✅ {source_name}: Inserted {len(normalized)} offers "
                    f"(snapshot_id={snap_id})"
                )
            else:
                stats.sources_failed += 1
                
        except Exception as e:
            # Source-level error (fetch, database, etc.)
            error_msg = str(e)
            logger.error(f"❌ {source_name}: Source error: {error_msg}")
            stats.sources_failed += 1
            stats.parse_errors.append({"source": source_name, "error": error_msg})
            
            # Best-effort: try to record the failure
            try:
                source_id = sb.upsert_source(src)
                sb.insert_snapshot({
                    "run_id": run_id,
                    "source_id": source_id,
                    "http_status": 0,
                    "raw_text": None,
                    "raw_json": None,
                    "parse_status": "error",
                    "parse_error": error_msg,
                })
            except Exception:
                pass  # Give up on recording this error
    
    # Determine final run status
    if stats.sources_success >= stats.sources_enabled:
        final_status = "success"
    elif stats.sources_success > 0:
        final_status = "partial"
    else:
        final_status = "failed"
    
    # Finish run
    sb.finish_run(run_id, status=final_status, stats=stats.to_dict())
    
    logger.info(
        f"🏁 Run {run_id} finished with status={final_status}\n"
        f"   Sources: {stats.sources_enabled} enabled, "
        f"{stats.sources_success} success, "
        f"{stats.sources_failed} failed, "
        f"{stats.sources_skipped} skipped\n"
        f"   Offers inserted: {stats.offers_inserted}"
    )
    
    return {
        "run_id": run_id,
        "status": final_status,
        "stats": stats.to_dict(),
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Mortgage rate collector - fetch and parse rates from lenders"
    )
    parser.add_argument(
        "--run-type",
        choices=["real", "sample"],
        default=os.environ.get("RUN_TYPE", "real"),
        help="Type of run: 'real' (default) or 'sample' for demo data"
    )
    parser.add_argument(
        "--sources",
        default=None,
        help="Path to sources.yaml file (default: sources.yaml in cwd)"
    )
    
    args = parser.parse_args()
    
    try:
        result = run_collector(run_type=args.run_type, sources_path=args.sources)
        
        # Exit with appropriate code
        # Both "success" and "partial" are considered successful runs
        # Partial means at least one source succeeded (which is good!)
        if result["status"] in ["success", "partial"]:
            sys.exit(0)
        else:
            # Only fail if NO sources succeeded
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
