"""
Non-monetary guardrail + category normalizer for InsightSchemaV2.
Maps raw model output to canonical friction categories.
"""

# Canonical friction categories in V2
VALID_FRICTION_CATEGORIES = {
    'Fit/Size', 'Fabric/Material', 'Trust/Authenticity',
    'Styling/Occasion', 'Social-Validation', 'Delivery/Return', 'UX/App', 'None'
}

# Any price/monetary label → remap to Trust/Authenticity or None
# (The system focuses on non-monetary conversion blockers)
MONETARY_REMAPS = {
    'Price/Value':      'Trust/Authenticity',
    'Price':            'Trust/Authenticity',
    'Discount':         'Trust/Authenticity',
    'Cost':             'Trust/Authenticity',
    'Affordability':    'Trust/Authenticity',
}

# Typo / variant normalizer
VARIANT_NORMALIZER = {
    'Fit':          'Fit/Size',
    'Size':         'Fit/Size',
    'Sizing':       'Fit/Size',
    'Fabric':       'Fabric/Material',
    'Material':     'Fabric/Material',
    'Quality':      'Fabric/Material',
    'Trust':        'Trust/Authenticity',
    'Authenticity': 'Trust/Authenticity',
    'Styling':      'Styling/Occasion',
    'Occasion':     'Styling/Occasion',
    'Social':       'Social-Validation',
    'Validation':   'Social-Validation',
    'Delivery':     'Delivery/Return',
    'Return':       'Delivery/Return',
    'UX':           'UX/App',
    'App':          'UX/App',
}


def enforce_non_monetary_guardrail(friction_category: str) -> str:
    """
    1. Remap any monetary categories to non-monetary equivalents.
    2. Normalize variants/typos.
    3. Default to 'None' if unrecognized.
    """
    if not friction_category:
        return 'None'

    # Direct monetary remap
    if friction_category in MONETARY_REMAPS:
        return MONETARY_REMAPS[friction_category]

    # Already valid
    if friction_category in VALID_FRICTION_CATEGORIES:
        return friction_category

    # Try variant normalization
    normalized = VARIANT_NORMALIZER.get(friction_category)
    if normalized:
        return normalized

    # Unknown — default to None
    return 'None'
