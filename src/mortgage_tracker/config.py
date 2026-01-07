import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
import yaml


@dataclass
class Defaults:
    state: str = "MA"
    loan_amount: int = 600000
    ltv: int = 80
    fico: int = 760
    lock_days: int = 30


@dataclass
class Config:
    supabase_url: str
    supabase_service_role_key: str
    email_provider_key: Optional[str]
    defaults: Defaults
    sources: list


def load_config(sources_path: str = "sources.yaml") -> Config:
    load_dotenv()

    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    email_key = os.environ.get("EMAIL_PROVIDER_KEY", None)

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    with open(sources_path, "r") as f:
        data = yaml.safe_load(f) or {}

    d = data.get("defaults", {})
    defaults = Defaults(
        state=os.environ.get("DEFAULT_STATE", d.get("state", "MA")),
        loan_amount=int(os.environ.get("DEFAULT_LOAN_AMOUNT", d.get("loan_amount", 600000))),
        ltv=int(os.environ.get("DEFAULT_LTV", d.get("ltv", 80))),
        fico=int(os.environ.get("DEFAULT_FICO", d.get("fico", 760))),
        lock_days=int(os.environ.get("DEFAULT_LOCK_DAYS", d.get("lock_days", 30))),
    )

    sources = data.get("sources", [])

    return Config(
        supabase_url=supabase_url,
        supabase_service_role_key=supabase_key,
        email_provider_key=email_key,
        defaults=defaults,
        sources=sources,
    )
