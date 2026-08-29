"""Descriptor vocabularies, per domain. Pure data, no logic.

See DECISIONS.md D-001 (beer vocabulary) and D-014 (shared axes).
Nothing here is settled; these lists are a starting point, not a schema.
"""

# The shared core: axes believed to mean the same thing in every domain.
# The cross-domain transfer story (docs/11) rests entirely on this being true.
# UNTESTED ASSUMPTION.
SHARED_AXES = [
    "sweetness",
    "bitterness",
    "body",
    "acidity",
    "intensity",
    "alcohol_heat",
    "fruitiness",
    "smoke_oak",
]

# Domain tails. Axes that only make sense inside one domain.
DOMAIN_AXES = {
    "beer": ["hoppy", "malty", "floral", "astringent", "roasty"],
    "whisky": ["smoky", "medicinal", "honey", "nutty", "winey", "spicy"],
    "wine": ["tannin", "minerality", "earthiness"],
}

# Measured facts. Never inferred when they can be looked up.
HARD_NUMERICS = {
    "beer": ["abv", "ibu", "srm"],
    "whisky": ["abv", "age_years"],
    "wine": ["abv", "vintage"],
}


def axes_for(domain: str) -> list[str]:
    """Full ordered axis list for a domain: shared core, then domain tail."""
    return SHARED_AXES + DOMAIN_AXES[domain]
