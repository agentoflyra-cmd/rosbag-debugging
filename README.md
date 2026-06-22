# rosbag-debugging

Diagnose ROS 1/ROS 2 rosbag playback failures — SLAM divergence, localization drift, tracking loss, TF issues, sensor sync problems, and regression analysis.

## Structure

```
SKILL.md          — Skill definition for OpenCode agents
agents/           — Agent configuration (OpenAI compat)
references/       — Case studies and review checklist
scripts/          — Triage and analysis scripts
```

## Quick start

```sh
python3 scripts/triage_rosbag_run.py test_runs/rosbag_slam --latest
```

## Methodology

Find the **first causal failure**, not the loudest downstream symptom. Build a time-ordered chain from input/mode changes through estimator state, recovery behavior, and final divergence.

See `references/review-checklist.md` for the full debugging workflow.
