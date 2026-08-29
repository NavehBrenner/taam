# 13 — Source Terms, Scraping, and the Untappd Problem

Written because the repo is public (ADR-0001), which raises the stakes on getting
this right, and because **Untappd's API terms conflict with this project's
architecture more sharply than expected.**

## The finding

Untappd's API terms of service, read directly, say roughly this:

| Clause | Text (paraphrased) | Conflicts with |
|---|---|---|
| **Cache expiry** | applications storing Untappd data **must delete their caches every 24 hours** | N-02 (permanent local cache), and the whole rate-limit survival strategy |
| **No own database** | you may not use the API **to build your own beer database** | the `item` table (§04), which is literally a beer database |
| **No mining or analytics** | you may not **"mine, analyze or provide analytics"** — to third parties *or to yourself* | the entire project |
| **No resale/redistribution** | may not sell, rent or trade data acquired from the API | (fine — we don't) |
| **Attribution** | must display "Powered by Untappd" / "Data provided by Untappd" | (fine — trivial) |
| **Documented endpoints only** | undocumented/private API use → **immediate suspension of key and account**, "strictly monitored" | any scraping |
| **Rate limits** | 100/hr, and circumventing limits revokes access | (already designed around) |

The three rows in bold are not edge cases. **"Do not build your own beer
database" and "do not mine or analyze" describe this project.**

## What this actually means

Be honest about the two separate questions.

**Legally**, for a personal, non-commercial project: the exposure is negligible.
Terms of service are a contract, not criminal law; scraping public data has not
been a computer-crime matter in the US since *hiQ v. LinkedIn* and *Van Buren*.
Nobody sues a student over a beer app. The realistic worst case is an account and
API-key ban.

**Practically**, three things follow, and they matter:

1. **Untappd cannot be the backbone of the catalog.** Not because of legal risk,
   but because a source we must purge every 24 hours cannot be a permanent local
   store, and 100 calls/hour with no cache is unusable. This is a design
   constraint, not a compliance footnote.
2. **A public repo is different from a private one.** Nobody audits a private
   project. A public repo named in a search for "untappd scraper" is a
   findable, citable ToS violation attached to your real name and your portfolio.
   The asymmetry is the point: the downside is reputational and permanent, the
   upside is saving a few hours of catalog work.
3. **Their enforcement lever is the account, not the courts.** "Strictly
   monitored", "immediate suspension of API keys and associated accounts" — and
   the associated account may be a personal Untappd account with years of
   check-ins in it.

## Policy for this repo

1. **No scraper code in this repository.** Not disabled, not commented out, not
   behind a flag. A public repo with a scraper in it is the specific thing worth
   avoiding, and there is no version of it that is worth a few hours saved.
2. **Untappd is used through the documented API only**, with attribution, inside
   the rate limit.
3. **The permanent local catalog is built from sources whose terms allow it** —
   beer.db (public domain), catalog.beer (check its terms explicitly), and
   manual entry. These are the backbone.
4. **Untappd is used for what only it can give**, fetched on demand and held
   under its cache rules: community score and coverage of Israeli beers that
   nothing else has.
5. **Anything Naveh enters by hand is his own data** and is not subject to
   anyone's terms. The manual/photo path (D-005 option C) is not just a coverage
   fallback — it is the clean-title path.

## Consequences worth propagating

- **D-004** — catalog.beer and beer.db move from "primary and bulk seed" to
  "the only permanent stores". Untappd demotes to an on-demand enrichment source.
- **D-005** — the manual/photo entry path gets **more** important, not less.
- **§04 data model** — `community_score` needs a `fetched_at` and a policy for
  what happens when it ages out, rather than being stored indefinitely.
- **§10 evaluation** — the B1 baseline depends on community scores. If those
  can't be retained, B1 has to be computed at fetch time and only the *result*
  kept, not the underlying data.

## Open questions

- **What exactly do catalog.beer's terms say?** Unchecked. If they permit
  permanent storage, they become the backbone and this problem mostly resolves.
  **Check before building on it.**
- Is there a legitimate source of community scores with sane retention terms?
  BeerAdvocate? The 2011 academic dumps are explicitly research-licensed and are
  fine — but they're 2011.
- Does the `α` (community) term actually earn its place, given this friction? If
  the personal model is decent without it, the simplest fix to the whole problem
  is to drop the term. **Worth measuring before designing around it.**

## The general rule

For every source, before writing an adapter, record in this file: what the terms
permit, what they forbid, whether derived data may be retained, and whether
attribution is required. It is ten minutes per source and it is the difference
between a portfolio project and a liability.
