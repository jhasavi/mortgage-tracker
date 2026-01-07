"""Data quality validation for mortgage rate offers."""
import logging
from typing import List, Dict, Any

logger = logging.getLogger("mortgage_tracker.validate")


def validate_offer(offer: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate a single mortgage offer for data quality.
    
    Returns:
        (is_valid, list_of_issues)
    """
    issues = []
    
    # Required fields
    required_fields = ['lender_name', 'category', 'rate', 'apr']
    for field in required_fields:
        if field not in offer or offer[field] is None:
            issues.append(f"Missing required field: {field}")
    
    # Rate validation
    rate = offer.get('rate')
    if rate is not None:
        if rate <= 0 or rate > 20:
            issues.append(f"Invalid rate: {rate}% (expected 0-20%)")
        if rate < 2:
            issues.append(f"Suspiciously low rate: {rate}%")
    
    # APR validation
    apr = offer.get('apr')
    if apr is not None:
        if apr <= 0 or apr > 20:
            issues.append(f"Invalid APR: {apr}% (expected 0-20%)")
        if apr < 2:
            issues.append(f"Suspiciously low APR: {apr}%")
        
        # APR should be >= rate
        if rate is not None and apr < rate:
            issues.append(f"APR ({apr}%) is less than rate ({rate}%) - likely parsing error")
    
    # Points validation
    points = offer.get('points')
    if points is not None:
        if points < 0 or points > 10:
            issues.append(f"Invalid points: {points}% (expected 0-10%)")
    
    # Category validation
    category = offer.get('category')
    valid_categories = ['30Y fixed', '15Y fixed', '20Y fixed', '10Y fixed',
                       '5/6 ARM', '7/6 ARM', '10/6 ARM',
                       'FHA 30Y', 'VA 30Y']
    if category and category not in valid_categories:
        issues.append(f"Unknown category: {category}")
    
    return (len(issues) == 0, issues)


def validate_offers(offers: List[Dict[str, Any]], lender_name: str = None) -> Dict[str, Any]:
    """
    Validate a list of offers and return summary.
    
    Returns:
        {
            'total': int,
            'valid': int,
            'invalid': int,
            'issues': List[str]
        }
    """
    total = len(offers)
    valid_count = 0
    all_issues = []
    
    for i, offer in enumerate(offers):
        is_valid, issues = validate_offer(offer)
        if is_valid:
            valid_count += 1
        else:
            prefix = f"{lender_name or offer.get('lender_name', 'Unknown')} offer #{i+1}: "
            all_issues.extend([prefix + issue for issue in issues])
    
    result = {
        'total': total,
        'valid': valid_count,
        'invalid': total - valid_count,
        'issues': all_issues
    }
    
    # Log summary
    if total > 0:
        logger.info(f"Validation: {valid_count}/{total} valid offers")
        if all_issues:
            for issue in all_issues[:10]:  # Show first 10 issues
                logger.warning(f"  {issue}")
            if len(all_issues) > 10:
                logger.warning(f"  ... and {len(all_issues) - 10} more issues")
    
    return result
