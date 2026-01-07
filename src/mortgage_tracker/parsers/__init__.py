"""
Parser registry for mortgage rate collectors.

Each parser must implement the BaseParser interface and return a list of offer dicts.
Register new parsers here to make them available to the main collector.
"""
from typing import Dict, Type
from .base import BaseParser

# Import all parsers
from .dcu import DCUParser
from .example_html_table import ExampleHtmlTableParser
from .example_json_endpoint import ExampleJsonEndpointParser
from .metro_cu import MetroCUParser
from .rockland_trust import RocklandTrustParser
from .navy_federal import NavyFederalParser
from .penfed import PenFedParser
from .alliant import AlliantParser

# Import real parsers (add more as we build them)
# TODO: Add more parsers as they are implemented

# Parser registry: maps parser_key -> Parser class
PARSER_REGISTRY: Dict[str, Type[BaseParser]] = {
    # Working parsers
    'dcu': DCUParser,
    'navy_federal': NavyFederalParser,
    'penfed': PenFedParser,
    'alliant': AlliantParser,
    
    # Real parsers (quote-flow only, typically return empty)
    'metro_cu': MetroCUParser,
    'rockland_trust': RocklandTrustParser,
    
    # Example parsers
    'example_html_table': ExampleHtmlTableParser,
    'example_json_endpoint': ExampleJsonEndpointParser,
    
    # TODO: Add more parsers as needed
}

def get_parser(parser_key: str) -> BaseParser:
    """
    Get a parser instance by key.
    
    Args:
        parser_key: The parser identifier from sources.yaml
        
    Returns:
        An instance of the requested parser
        
    Raises:
        KeyError: If parser_key is not registered
    """
    if parser_key not in PARSER_REGISTRY:
        available = ', '.join(PARSER_REGISTRY.keys())
        raise KeyError(
            f"Parser '{parser_key}' not found. Available parsers: {available}"
        )
    
    parser_class = PARSER_REGISTRY[parser_key]
    return parser_class()

__all__ = ['PARSER_REGISTRY', 'get_parser', 'BaseParser']
