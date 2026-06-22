# rosbag-debugging

Diagnose ROS 1/ROS 2 rosbag playback failures — SLAM divergence, localization drift, tracking loss, TF issues, sensor sync problems, and regression analysis.

## Structure

```
SKILL.md          — Full methodology and workflow
agents/           — AI agent configuration (optional)
references/       — Case studies and review checklist
scripts/          — Triage and analysis scripts
```

## Quick start

```sh
python3 scripts/triage_rosbag_run.py test_runs/rosbag_slam --latest
```

## Methodology

Find the **first causal failure**, not the loudest downstream symptom. Build a time-ordered chain from input/mode changes through estimator state, recovery behavior, and final divergence. Avoid threshold-tuning isolated warnings — trace the root event that triggered the cascade.

See `references/review-checklist.md` for the step-by-step debugging workflow.

## Requirements

- Python 3.8+
- Standard library only (no external deps for triage script)
