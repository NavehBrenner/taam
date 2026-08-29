# Glossary

Written so that future-you doesn't have to re-read the modelling docs to follow
a conversation.

**Item** — anything drinkable that can be profiled and rated. A beer, a whisky,
a wine. Deliberately not called "beer" anywhere in the code.

**Domain** — beer, whisky, wine. Determines the descriptor vocabulary and the
catalog source, and nothing else.

**Profile** — the fixed-length sensory vector for an item. `[shared axes |
domain axes]`. This is what the model consumes. It is a property of the *item*
and never of the person.

**Palate** (`w_you`) — the learned weight vector mapping a profile to your
rating. This is a property of *you*. The readable version of it is the main
non-model-y output of the project.

**Descriptor / axis** — one dimension of a profile, e.g. `bitter`, `body`.

**Hard numerics** — measured facts about an item: ABV, IBU, SRM. Distinguished
from descriptors because they are exact and should never be inferred when they
can be looked up.

**Community score** — the public aggregate rating of an item. Used as the
population term in the decomposition, not as a recommendation.

**Decomposition** — `rating ≈ α·community + w·profile + b`. The mechanism that
makes the system useful at N=0 and personal at N=50 without a discontinuity.

**Population prior** — a distribution over plausible palates, estimated from many
real users' rating histories. What makes learning from 10 samples defensible.

**Context / mood** — the situation of a check-in: time, food, company, weather,
intent. Logged always, modelled later.

**Offset** (`δ_m`) — the per-mood adjustment to the palate vector.

**Exploration weight** — how much the recommender prefers uncertain items over
high-scoring ones. The knob behind "feeling exploratory".

**Crossover N** — the number of check-ins at which the personal model starts
beating the best dumb baseline. The project's headline number.

**Kill criterion** — a pre-registered observation that would tell us an approach
is wrong. Every milestone has one.
