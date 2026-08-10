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

Each field contains `source: exemplar | rule`, `confidence`, and a typed `value`:

- sentence-length range and minimum standard deviation;
- paragraph length and sentences per paragraph;
- paragraph-opening distribution;
- connective density and allowed connective set;
- active/passive ratio by section type;
- first-person frequency;
- hedge density and maximum hedge layers;
- usual claim-sentence position within a paragraph;
- contribution and limitation moves as structural labels, never verbatim templates.

## Private storage

Actual target values are unpublished derivatives. Store them only at `<paper_dir>/.helicon/style/target_profile.json`; store the screening decision at `target_screening.json`. Never commit either file, revision-direction reports, hold-out manifests, or filled exemplar cards to this repository.

The repository contains only this policy, schemas expressed by the generator output, and an empty card template. `check_core_contamination.py` rejects private target artifacts found inside the skill repository.

## Exemplar cards

Store filled cards only in `<paper_dir>/.helicon/style/exemplars/`. For P4, P5, or P6, load at most 3 cards that match both section type and rule identifier. Use them as form anchors only: never copy a paragraph, sentence, claim, number, citation, project term, or result from a card.

Reviewer-driven stage pairs remain visible in direction reports but are excluded from author-preference frequencies unless the author explicitly reclassifies them. An unchanged expression can enter `Expressions the user likes` only after the author confirms it.
