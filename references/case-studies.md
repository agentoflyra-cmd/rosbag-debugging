# Case Studies from FAST-LIO Localization Debugging

## Contents

1. Convergence is not correctness
2. Degree/radian mismatch creates false correction rejection
3. Last-good is not previous-frame
4. Mode leakage creates false Mapping loss
5. Periodic GICP stalls resemble synchronization failure
6. Recovery success can mask continuing estimator corruption
7. Visualization warnings are not automatically estimator failures
8. Ray clearing can damage static geometry

## 1. Convergence is not correctness

Observed candidate:

```text
coarse_has_converged=true coarse_fitness=20
```

`hasConverged()` only says the optimizer terminated according to its numerical
criteria. It does not prove geometric alignment. Inspect fitness, overlap,
correspondence count, final transform and deviation from the hint. Only consider
loosening a threshold when the candidate is near the threshold and companion
metrics remain healthy.

## 2. Degree/radian mismatch creates false correction rejection

The estimator used `SO3ToEuler()`, which returned degrees, then passed the
difference to a radian normalizer and compared it with a five-degree threshold
stored in radians. Logs reported normal corrections as roughly 5–11 degrees
and rejected them continuously.

Diagnostic pattern:

```text
Hint localization succeeded ... fine_fitness=0.034
LiDAR correction gated ... yaw_delta=6.89deg
...
Tracking lost ... no_effective_frames=3
```

The position corrections were only millimeters, contradicting an immediate
catastrophic match failure. Reading the conversion function exposed the unit
defect. The fix was to compute yaw directly in radians from the rotation matrix.

Lesson: audit producer units, not variable names or log suffixes.

## 3. Last-good is not previous-frame

A health check compared current yaw to `last_good_rotation_`. It updated
`last_good_rotation_` only when a frame was fully good. During a normal turn,
accumulated yaw eventually exceeded 15 degrees. Every later frame remained bad
because the reference never advanced.

Evidence:

```text
Tracking lost: residual=0.033 ratio=0.607 bad_frames=10
mode=localization yaw_jump=48.56
```

Residual and effective ratio were healthy. Recovery repeatedly achieved fine
fitness around `0.04`, yet loss returned after ten frames. The correct jump
reference was the immediately previous processed pose; last-good remained
useful only as a recovery seed.

Lesson: define whether a threshold limits derivative, discontinuity, drift from
an anchor, or accumulated motion.

## 4. Mode leakage creates false Mapping loss

Yaw-jump health logic intended for matching against a fixed loaded map also ran
during Mapping:

```text
Tracking lost: residual=0.040 ratio=0.766 mode=mapping yaw_jump=36.60
```

The healthy residual and ratio showed that mapping itself had not lost
constraints. Restricting correction gating and tracking-loss transitions to
Localization restored Mapping behavior.

Lesson: include runtime mode in every state-machine warning and audit branch
ownership explicitly.

## 5. Periodic GICP stalls resemble synchronization failure

The robot appeared to pause every few steps. There were no input timestamp
regressions or missing-IMU warnings. After tracking loss, logs showed one local
recovery attempt approximately every second, matching:

```yaml
relocalization:
  attempt_interval_sec: 1.0
```

GICP ran synchronously on the processing path, producing periodic stalls.
Moving it off the odometry path improves responsiveness, but the earlier false
tracking-loss trigger still had to be fixed.

Lesson: correlate stall period with configured timers before blaming sensor
synchronization.

## 6. Recovery success can mask continuing estimator corruption

Repeated lines such as:

```text
Auto relocalization succeeded ... fine_fitness=0.038
Tracking lost ...
Auto relocalization succeeded ... fine_fitness=0.041
```

show that registration can recover map-to-odom while the tracking watchdog or
EKF handoff immediately breaks it again. Do not interpret frequent recovery
success as robust tracking. Inspect the first frames after each successful
handoff.

## 7. Visualization warnings are not automatically estimator failures

RViz reported:

```text
Message Filter dropping message ... timestamp ... earlier than all the data in
the transform cache
```

This can explain missing or delayed visualization, but does not prove the
FAST-LIO sensor synchronizer failed. Compare estimator input logs, message
header times, `/clock`, and TF publication independently.

Lesson: separate rendering, transport, synchronization and estimator state.

## 8. Ray clearing can damage static geometry

During mapping, ray-based clearing removed previously observed faces of narrow
pillars when later rays passed beside or behind the near face. This is a map
maintenance/visibility-model issue, not a localization fitness issue.

Potential remedies include endpoint protection, visibility-aware occupancy,
temporal confirmation and a multi-view pillar regression bag.

Lesson: preserve unrelated observations as explicit known issues instead of
mixing them into the active localization diagnosis.

