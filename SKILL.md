---
name: rosbag-debugging
description: Diagnose ROS 1/ROS 2 rosbag, SLAM, localization, mapping, TF, sensor synchronization, navigation, and playback failures by correlating run logs, bag metadata, state transitions, numeric invariants, timing, and source code. Use when a run drifts, jumps, flies outside the map, loses tracking, repeatedly relocalizes, stalls periodically, drops messages, fails to save or display a map, behaves differently live versus playback, or needs an evidence-based rosbag regression review.
---

# ROS Bag Debugging

Find the first causal failure, not the loudest downstream symptom. Build a
time-ordered chain from input and mode changes through estimator state,
recovery behavior, and final divergence.

## Start with the run artifact

1. Locate the newest relevant run instead of assuming the path:

   ```sh
   find test_runs -type f -name '*.log' -printf '%T@ %p\n' | sort -nr | head
   ```

2. Run the bundled triage script on a run directory or a root containing runs:

   ```sh
   python3 skills/rosbag-debugging/scripts/triage_rosbag_run.py \
     test_runs/rosbag_slam --latest
   ```

3. Inventory logs, status snapshots, generated configs, maps, TF captures, and
   bag metadata. Record exact configuration copied into the run directory;
   do not rely on the current source-tree YAML.

4. If only a bag is available, inspect it read-only:

   ```sh
   ros2 bag info <bag>
   ```

   Check topic types, counts, duration, storage format, compression, and clock
   usage before replaying it.

## Build one causal timeline

Extract these event classes with timestamps:

- process start, bag pause/resume, `/clock`, mode and control commands;
- IMU initialization and first usable LiDAR scan;
- map load/save/index build and frame IDs;
- initial hint, candidate scores, consistency checks, acceptance;
- estimator correction gates and health metrics;
- tracking loss, recovery attempts, recovery acceptance and rejection;
- TF extrapolation, queue overflow, timestamp regression and buffer reset;
- process death, signal, save completion and test termination.

Anchor analysis at the first frame where a valid invariant becomes invalid.
Inspect 20–100 lines before that event. Later `No Effective Points`, huge
geometry deltas, and repeated recovery failures are usually consequences.

## Separate clocks

Keep these clocks distinct:

- wall/process log time;
- ROS time from `/clock`;
- message header time;
- per-point or scan-relative time;
- algorithm interval timers.

Do not call an issue “sensor synchronization” from visual delay alone. Require
evidence such as timestamp regression, missing IMU coverage for a scan,
abnormal scan duration, growing callback queues, stale TF at the message
timestamp, or reproducible input/output latency.

Periodic stalls are especially diagnostic. Measure their interval and compare
it with configured timers such as recovery attempts, map rebuilds, status
publishing, or save operations. A one-second stall paired with a one-second
synchronous GICP retry is compute blocking, not necessarily sensor sync.

## Check invariants before thresholds

Verify:

- units: radians versus degrees, seconds versus milliseconds/nanoseconds;
- frame semantics: map, odom, base, IMU and LiDAR;
- transform direction and composition order;
- current frame versus last frame versus last-good/reference frame;
- mode ownership: Mapping, Waiting, Relocalizing and Localization;
- state and covariance are restored together after rejected updates;
- loaded global map remains immutable during localization;
- recovery acceptance does not write a map-frame pose into an odom-frame EKF;
- health counters identify the actual failing gate.

Treat healthy companion metrics as contradiction evidence. For example,
`residual=0.033` and `effective_ratio=0.607` contradict a generic “poor ICP”
diagnosis when loss is attributed only to a large yaw jump.

## Classify the failure

Use this order:

1. Input validity and timestamp ordering.
2. Initialization and mode transition.
3. Frame/transform correctness.
4. Estimator correction and state continuity.
5. Health-monitor logic and counter semantics.
6. Recovery quality and state handoff.
7. Performance/blocking and queue growth.
8. Visualization-only warnings.

Do not tune fitness, overlap, jump, or failure-count thresholds until code
semantics and units have been checked.

## Trace evidence back to code

Search exact log text first:

```sh
rg -n 'Tracking lost|correction gated|Auto relocalization' .
```

Then inspect:

- where each logged quantity is computed;
- its type, unit and reference frame;
- when its reference value is updated;
- which runtime modes execute the branch;
- what happens after rejection or recovery;
- whether expensive work runs on the odometry callback thread.

Form one falsifiable hypothesis and predict the next-run log change before
editing code.

## Validate proportionally

After a fix:

1. Run static checks and compile the affected package.
2. Replay the same bag and compare the first-failure timestamp.
3. Confirm the targeted event disappears without hiding real failures.
4. Run a perturbed case: different hint, start offset, turn, corridor, or loss.
5. Report remaining risks separately from the fixed causal chain.

For detailed examples derived from real localization failures, read
[references/case-studies.md](references/case-studies.md). For a compact
evidence checklist and report template, read
[references/review-checklist.md](references/review-checklist.md).

## Report format

Lead with:

1. first causal event and exact timestamp/line;
2. evidence chain;
3. ruled-out alternatives;
4. implicated code and semantic defect;
5. proposed fix and expected next-run evidence;
6. validation performed and unresolved risks.

Distinguish facts from inference. Never claim a bag proves physical ground
truth unless an independent reference trajectory or landmark measurement is
available.

