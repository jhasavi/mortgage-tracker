from typing import List, Dict, Any, Optional


class BaseParser:
    """Interface for parsers. Implement parse() to return raw offer dicts."""

    def parse(self, *, text: Optional[str] = None, js: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError
