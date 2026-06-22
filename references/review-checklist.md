# Rosbag Review Checklist

## Artifact inventory

- Exact run directory and modification time
- Bag path, storage format, compression, duration and topic counts
- Generated runtime configuration, not only repository defaults
- Mapping, localization, control, playback and navigation logs
- Status snapshots, TF captures, odometry captures and saved map
- Git revision and dirty changes when available

## Timeline table

| Time | Mode | Input/state event | Quality metrics | Decision | Consequence |
|---|---|---|---|---|---|
| | | | | | |

Always include the last known-good event and the first bad event.

## Numeric audit

- Quantity name
- Logged value
- Source expression
- Unit
- Frame/reference
- Threshold unit
- Update/reset policy
- Finite/range checks

## Timing audit

- LiDAR rate and scan duration
- IMU rate and coverage around each scan
- Playback rate and `/clock`
- Callback processing duration
- Recovery/map-build/save duration
- Repeated warning interval
- Queue depth or message drops

## Hypothesis test

Write each candidate as:

> If cause X is true, evidence Y must appear before symptom Z.

Reject hypotheses contradicted by healthy metrics or event ordering.

## Recommended final response

```text
Root cause:
  <first causal defect>

Evidence:
  <timestamp/line and values>
  <causal sequence>

Not the cause:
  <alternatives ruled out and why>

Fix:
  <smallest semantic change>

Expected next run:
  <specific log/events that should disappear or change>

Remaining risk:
  <performance, coverage or unverified physical assumptions>
```

