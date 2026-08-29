"""Palate — personal preference learning for drinks.

Layering rule (see docs/03-architecture.md):

    domains/, catalog/, profiler/   MAY know what beer is.
    preference/, recommend/         MUST NOT.

If a change under preference/ or recommend/ mentions beer, whisky or wine,
the abstraction has leaked and the multi-domain plan (docs/11) is in trouble.
"""

__version__ = "0.0.0"
