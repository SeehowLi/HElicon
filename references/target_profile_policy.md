# Target Profile Policy

The target profile records an author-approved finished form. It is prescriptive and remains separate from the descriptive personal baseline.

| Property | Baseline | Target profile |
|---|---|---|
| Meaning | Current author habits | Author-approved finished form |
| Sample requirement | At least 5 distinct papers | At least 1 screened exemplar |
| Reason | Drift needs cross-paper variance | Direction does not require variance |
| Use | P6 drift detection | P4, P5, and P6 convergence target |
| Three stages of one paper | `thin(n=1)` | Sufficient after screening |

Never merge these objects. A target profile never enables a drift warning, and a thin baseline never blocks movement toward a qualified target.

## Venue dimension

Every generated target profile records the venue represented by its screened exemplar. Keep targets separated by venue; do not pool values from different venues into one field estimate. When the active paper uses the same venue, the normal field-level screening determines `target:ok` or `target:partial`. When a target is reused for another venue, force `target:partial` even if every field came from the exemplar, and apply the applicable register guidance in `venue_profiles.md`. The venue field selects applicability only; it never changes baseline qualification or enables drift alerts.

## Screen before use

Run `scripts/build_target_profile.py` before treating a final version as an exemplar. The screening is deterministic:

Inputs are ordered `.tex`, `.md`, or `.txt` stages. Convert PDF stages to private `.txt` files with the existing `extract_pdf_text.py`; the target scripts remain stdlib-only and do not add a PDF dependency.

1. compute P5 rule hits per 1000 words with `check_ai_tells.py`;
2. compute all structural metrics with `style_fingerprint.py`;
3. decide each dimension from fixed rule hits and sample-health checks;
4. mark every accepted field `source: exemplar` and every rejected field `source: rule`;
5. preview the table and profile before any write.

threshold: sentence-length targets require at least 4 sentences and a standard deviation of at least 4 words.

threshold: paragraph targets require at least 2 paragraphs.

threshold: connective targets require no Rule 5 finding and connective density no greater than 0.6 per sentence.

threshold: opening-structure targets require at least 2 observed opening types; active/passive targets require at least 4 sentences; first-person targets require at least 50 words.

threshold: hedging, claim-position, and contribution/limitation targets require at least one observation of the corresponding feature.

Rule 3 must have zero hits. A dimension associated with another numbered rule is rejected when that rule has any hit in the screened exemplar. These are qualification thresholds, not unpublished target values.

## Required fields

The profile records `venue`, same-venue and cross-venue applicability, and fields. Each field contains `source: exemplar | rule`, `confidence`, and a typed `value`:

- sentence-length range and minimum standard deviation;
- paragraph length and sentences per paragraph;
- paragraph-opening distribution;
- connective density and allowed connective set;
- active/passive ratio by section type;
- first-person frequency;
- hedge density and maximum hedge layers;
- usual claim-sentence position within a paragraph;
- contribution and limitation moves as structural labels, never verbatim templates.

## Resolution and pass ownership

Normal revision routes do not read this file and guess which fields apply. They run `scripts/resolve_target_profile.py`, which validates the current `helicon-target-profile-v3`, selects the active venue, and exposes only the fields owned by the requested passes. P4 owns sentence length, multi-paragraph length, and paragraph openings; P5 owns connectives and hedging; P6 owns section-normalized voice and first-person use. Claim position and contribution/limitation moves are P2/upstream signals and cannot silently restructure a bare language-polish request. A v2 profile remains readable for migration, but its old all-sentence opening field and raw-heading voice field are excluded and force `target:partial` until the profile is rebuilt after author confirmation.

The resolver's privacy-safe trace contains hashes, field identifiers, sources, pass ownership, and the resolved status; it contains no target values or manuscript text. The event is `resolved`, not `injected`: the trace proves deterministic selection and availability to the revision context, while causal efficacy requires a separate target-on/target-off evaluation.

Resolution does not itself authorize an edit. `scripts/revision_preflight.py` compares only estimable selection metrics with explicit accepted bounds and emits `preserve|revise`. Target statistics describe an accepted region or a direction of correction; point observations such as one exemplar's density are never quotas. The trace distinguishes resolved eligible fields from fields actually evaluated by the preflight. Text already within every evaluated boundary, with no P5 rule finding, must remain unchanged. Missing, point-only, or inestimable fields reduce coverage rather than creating a reason to rewrite.

## Private storage

Actual target values are unpublished derivatives. Store them only at `<paper_dir>/.helicon/style/target_profile.json`; store the screening decision at `target_screening.json`. A write from a separate staging directory must pass explicit project-local `--profile-output` and `--screening-output` paths; never strand the active profile under the staging corpus. Never commit either file, traces, revision-direction reports, hold-out manifests, or filled exemplar cards to this repository.

The repository contains only this policy, schemas expressed by the generator output, and an empty card template. `check_core_contamination.py` rejects private target artifacts found inside the skill repository.

## Exemplar cards

Store filled cards only in `<paper_dir>/.helicon/style/exemplars/`. For P4, P5, or P6, load at most 3 cards that match both section type and rule identifier. Use them as form anchors only: never copy a paragraph, sentence, claim, number, citation, project term, or result from a card.

Reviewer-driven stage pairs remain visible in direction reports but are excluded from author-preference frequencies unless the author explicitly reclassifies them. An unchanged expression can enter `Expressions the user likes` only after the author confirms it.
