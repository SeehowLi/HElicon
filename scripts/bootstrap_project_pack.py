#!/usr/bin/env python3
"""Create a HElicon external project pack from templates.

Usage:
  bootstrap_project_pack.py /path/to/HElicon_workspace/projects PROJECT_NAME
"""
from pathlib import Path
import shutil
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: bootstrap_project_pack.py <projects_root> <project_name>")
        return 2
    projects_root = Path(sys.argv[1])
    name = sys.argv[2]
    project_dir = projects_root / name
    project_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "storyline.md": f"# {name} Storyline\n\n## One-sentence story\n\n## Problem framing\n\n## Existing gap\n\n## FHE-specific bottleneck\n\n## Key insight\n\n## Design summary\n\n## Contribution hierarchy\n\n## Target-venue positioning\n\n## Claims to avoid\n",
        "local_glossary.md": f"# {name} Local Glossary\n\n| Term | Preferred English | Avoid | Notes |\n|---|---|---|---|\n",
        "focused_references.md": f"# {name} Focused References\n\n",
        "experiment_notes.md": f"# {name} Experiment Notes\n\n",
        "draft_status.md": f"# {name} Draft Status\n\n",
        "reviewer_risks.md": f"# {name} Reviewer Risks\n\n",
        "accepted_phrasing.md": f"# {name} Accepted Phrasing\n\n",
        "memory_patch_log.md": f"# {name} Memory Patch Log\n\n",
        "evidence_map.csv": "claim_id,claim,evidence_type,evidence_detail,source_or_file,status,risk,next_action\nC1,,,,,,,\nC2,,,,,,,\nC3,,,,,,,\n",
        "project_brief.yaml": f"paper:\n  project_name: {name}\n  working_title:\n  target_venues: [USENIX Security, NDSS, ACM CCS, IEEE S&P]\n  primary_venue:\n  paper_type:\n\nproblem:\n  application_or_task:\n  security_privacy_goal:\n  threat_model_summary:\n  why_this_problem_matters:\n  why_existing_solutions_are_insufficient:\n\ntechnical_core:\n  dominant_bottleneck:\n  key_insight:\n  method_summary:\n  fhe_scheme_or_crypto_stack:\n  parameters_known:\n  leakage_boundary:\n\nclaims:\n  c1:\n  c2:\n  c3:\n\nexperiments:\n  workloads:\n  baselines:\n  metrics:\n  ablations:\n  current_results:\n\nwriting:\n  intended_story:\n  title_direction:\n  abstract_direction:\n  terminology_constraints:\n  known_weaknesses:\n\nrisks:\n  novelty_risk:\n  evidence_risk:\n  threat_model_risk:\n  evaluation_risk:\n  terminology_risk:\n",
    }
    for filename, content in files.items():
        path = project_dir / filename
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    print(f"Created project pack: {project_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
