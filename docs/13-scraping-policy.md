# 13 — Source Terms, Data Provenance, and the Untappd Question

Written because the repo is public (ADR-0001), and because working through this
properly shrank Untappd's role from "backbone" to "a narrow gap-filler we may not
need at all".

**Read this before writing any data-source adapter.**

---

## 1. The correction that started it

**No API returns flavour descriptors.** Not Untappd, not catalog.beer, not
anyone. There is no endpoint anywhere that hands you
`{bitter: 6.5, malty: 3, body: 7}`.

That is the entire reason the profiler exists:

```
Kaggle set (3.2k beers, LABELLED descriptor vectors) ──trains──► regressor
                                                                     │
        any beer's description + ABV + IBU + style ───────────────►  ▼
                                                          descriptor vector
```

Labels come from Kaggle. The model is ours. An external catalog contributes, at
most, *the description string we feed in*.

So the question is never "which API gives us descriptors". It is only "where do
we get name / brewery / style / ABV / IBU / a description, for beers sold near
Beer Sheva".

## 2. What Untappd's terms actually say

| Clause | Conflicts with |
|---|---|
| Applications storing Untappd data **must delete caches every 24 hours** | N-02 permanent cache |
| May not use the API **to build your own beer database** | the `item` table |
| May not **"mine, analyze or provide analytics"** — to third parties *or yourself* | the project |
| Undocumented/private API use → **immediate suspension of key and associated account**, "strictly monitored" | any scraping |
| Attribution required; no resale; rate limits enforced (100/hr) | (fine) |

## 3. Copyright: facts are free, expression is not

Under *Feist*, **facts are not copyrightable**. ABV, IBU, style, beer name,
brewery name are facts about the world. Israel's 2007 Copyright Act follows the
same idea/expression divide, and Israel has **no EU-style *sui generis* database
right** — which is the thing that would otherwise bite.

Two caveats:

- **Compilation copyright is separate.** *Feist* allows protection for a
  compilation whose *selection and arrangement* is original. Extracting facts
  about beers you looked up is clean; systematically cloning a whole catalog is
  a different posture — and is also the specific thing the terms name.
- **Prose descriptions are someone's writing.** They are the copyrightable part.
  Convenient, because they are also the part we need least: the regressor
  consumes a description and emits a vector. Keep the vector, discard the text.

## 4. Contract is an independent track — this is the part people get wrong

Even if data is 100% uncopyrightable, "you agreed not to do this and did it" is
its own claim that does not care about copyright.

*hiQ v. LinkedIn* is the case usually cited for "scraping public data is legal".
hiQ did win the CFAA question at the Ninth Circuit. But in **November 2022 the
district court granted LinkedIn summary judgment on breach of contract** — hiQ
had breached the anti-scraping terms — and it ended in a consent judgment with a
permanent injunction.

The lesson from the case people quote at you: **winning on "not a computer
crime" and "not copyrighted" still leaves the contract claim standing.**

And an API key is *clickwrap* — affirmative acceptance, the strongest form of
contract formation. Our position is worse than an anonymous page-scraper's, not
better.

## 5. Claim exists ≠ anyone acts on it

| Risk | Realistic level |
|---|---|
| Copyright suit over fact rows | ~zero |
| Contract claim | legally real; never pursued against an individual, non-commercial project |
| **API key revoked** | plausible |
| **Untappd account suspended** | plausible — and it's the one that costs something |

Nobody sues a student over a beer database. Damages are nil and the PR is
terrible. The enforcement lever is the account.

## 6. The documentation asymmetry

Worth stating plainly, because it decides the policy:

- **Documenting a scrape changes legal exposure by roughly nothing.** The facts
  stay uncopyrightable either way.
- **It changes enforcement exposure a lot.** A public repo under a real name
  saying "catalog scraped from Untappd" is exactly what someone at Untappd finds
  searching their own name on GitHub — against terms that promise "immediate
  suspension of API keys and associated accounts", "strictly monitored".

So *scrape it and document it publicly* is the one configuration that takes the
low-legal-risk path and staples the high-enforcement-risk path to it. Pick one:
either a private bootstrap nobody advertises, or a documented source whose terms
permit documenting.

**There is also a quality argument, separate from risk.** This is an ML
portfolio project; the first question a reader has is where the training data
came from. If the honest answer is one you'd rather leave out of the README,
that's a signal about the design, not about the risk. A data section you can
write in full, in public, with no asterisk, is worth more than a few hundred
rows.

## 7. The arithmetic: how much do we actually need?

A lookup is ~2 calls (search, then beer info). But **each beer is needed once,
ever** — fetch it, compute the profile vector, keep the vector and the facts,
discard the description.

So it is not "100 calls/hour forever". It is **2 calls, once, per beer
encountered in a lifetime.** ~500 distinct beers over several years ≈ 1,000
calls total. The ceiling is never approached.

The 24-hour cache rule helps rather than hurts here: it is cross-day retention
that is forbidden, and everything looked at within one shop trip is free to hold.

**The one case that strains it:** the shelf photo. 40 bottles → ~80 calls in one
burst. Fits the hour, but only just; a second fridge in the same hour throttles.
Design for it: batch, dedupe against what is already held, and degrade to
*"I can rank these 30, these 10 are unknown"* rather than failing.

Everything else is nowhere near: a menu of 8 taps ≈ 16 calls; one bottle in hand
= 2.

## 8. The label is a primary source

The most useful realisation in this whole thread.

**For Israeli beers, the bottle in your hand beats any API.** ABV is legally
required on the label. Style is usually printed. Name and brewery obviously.
That is most of a fact row — free, authoritative, offline, and attached to
nobody's terms.

## 9. The resulting fallback chain

```
local catalog (beer.db / catalog.beer)      free, permanent, citable
  ↓ miss
label OCR → facts straight off the bottle   yours, authoritative, works offline
  ↓ description still thin
Untappd, 2 calls, description only          the narrow remaining gap
  ↓ miss
type it yourself, ~30s                      always available
```

Untappd ends up filling a genuinely small slot: **prose descriptions for local
beers absent from the free catalogs.** Worth having; not worth architecting
around.

## 10. Policy for this repo

1. **No scraper code in this repository.** Not disabled, not behind a flag.
2. **Untappd through the documented API only**, with attribution, inside the
   rate limit, holding nothing past its cache window.
3. **The permanent catalog is built only from sources whose terms allow it** —
   beer.db (public domain), catalog.beer (terms unchecked — verify first), and
   hand-entered data, which is ours and subject to nobody's terms.
4. **Every source gets a row in §11 before an adapter is written.**
5. **Nothing that cannot be regenerated should be upstream of a result we care
   about.** The test for any bootstrap: could it be deleted tomorrow and the
   project still work? If no, it is load-bearing and built on sand.

## 11. Source register

Fill this in before writing each adapter. Ten minutes per source; the difference
between a portfolio project and a liability.

| Source | Retention allowed? | Redistribution? | Attribution? | Verified |
|---|---|---|---|---|
| Kaggle Beer Profile set | yes | per dataset licence | cite | ☐ |
| BeerAdvocate / RateBeer (UCSD) | yes, research use | no | cite papers | ☐ |
| beer.db | yes — public domain | yes | courtesy | ✅ *(but empty — DE-001)* |
| catalog.beer | **yes — CC BY 4.0** | **yes, incl. commercial** | **required** | ✅ |
| Untappd API | **no — 24h purge** | no | required | ✅ |
| Scotch whisky 86×12 set | yes | per source | cite | ☐ |
| Label OCR / manual entry | ours | ours | n/a | ✅ |

### catalog.beer — verified 2026-08-30 (NVB-78)

The blocking unknown is resolved, and it resolved in our favour.
<https://catalog.beer/terms> and <https://catalog.beer/api-usage> both state:

> "The content displayed on this website is licensed under a Creative Commons
> Attribution 4.0 International license (CC BY 4.0)." … "This license does not
> apply to any brewery's name, brand(s), or trademarks, which remain the
> property of their respective owners."

CC BY 4.0 grants *Share* ("copy and redistribute the material in any medium or
format") and *Adapt* ("remix, transform, and build upon the material for any
purpose, **even commercially**"), against a single obligation: give appropriate
credit, link the licence, and indicate if changes were made.

There is **no cache-purge clause, no "don't build your own database" clause, and
no anti-mining clause** — the three that make Untappd unusable as a store. Every
concern in §2 evaporates for this source.

**Required of us:** a CC BY 4.0 attribution for Catalog.beer wherever
catalog-derived rows appear (README, and any exported dataset), noting that
changes were made — the profiler transforms every row it touches.

**But the licence being permissive does not make the data useful.** See
`docs/05-data-sources.md`: 3 of 12 Israeli breweries present, 10 beers total,
and `description` empty on 10/10 of them. Clean terms over a nearly empty
shelf. catalog.beer is the backbone we are *allowed* to build — it is just a
much thinner backbone than the terms alone would suggest.

## 12. Open questions

- ~~**catalog.beer's terms.** The hinge.~~ **Settled 2026-08-30: CC BY 4.0.**
  Retention, redistribution and commercial use are all permitted. It becomes the
  permanent backbone; §2's problems apply to Untappd only. See §11 above.
- **Is Untappd's `beer_description` even populated for Israeli micro-breweries?**
  Still open, and now the most valuable unknown in the whole source strategy.
  NVB-78 raised its stakes rather than settling it: catalog.beer was *measured*
  to have no descriptions for Israeli beers, so Untappd is the last candidate
  source of prose for them. If it is empty too, **no source has a description
  for a local beer** — D-002 option B (the trained regressor) simply cannot run
  on the local tail, and the profiler must fall back to the LLM or to manual
  entry for every Israeli beer.

  **Why it is still unanswered:** it needs a registered API key, and the cheap
  way to answer it — reading Untappd beer pages directly — is exactly what §10.1
  forbids. It cannot be shortcut without violating this document.

  **The test, when a key exists:** `GET /v4/beer/info/{bid}` for ~20 Israeli
  beers across Tempo, IBBL, Biratenu, Sheeta, Beer Bazaar and Alexander; record
  `beer_description` length per beer. Verdict: median length under ~100
  characters, or more than half empty, means Untappd adds nothing the label does
  not, and **D-004 option D (drop Untappd entirely) becomes the answer** — which
  would also delete this entire document's problem.
- **Does the `α` community term earn its place at all?** If the personal model is
  decent without community scores, dropping the term removes this entire problem
  class in one line. M4 answers this anyway — measure before designing around it.

---

*Not legal advice — a careful read of well-known cases for a hobby project. Do
not rely on it if this ever becomes commercial.*
