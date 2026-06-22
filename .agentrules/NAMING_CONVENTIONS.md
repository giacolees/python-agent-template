# Naming Conventions — python-agent-template

These conventions are binding for all code, configs, and files generated or
modified in this repository, in addition to the rules in
[CODING_STANDARDS.md](CODING_STANDARDS.md).

## 1. Python identifiers

- **Modules / packages**: `snake_case`, short, no abbreviations that aren't
  domain-standard (`kalman_filter.py`, not `kf.py`).
- **Classes**: `PascalCase` (`TrackAssociator`, `RadarDetection`).
- **Functions / methods / variables**: `snake_case`
  (`compute_track_covariance`, `detection_threshold`).
- **Constants**: `UPPER_SNAKE_CASE`, module-level
  (`SPEED_OF_LIGHT_M_S`, `DEFAULT_CONFIG_PATH`).
- **Private helpers**: prefix with a single underscore (`_validate_bounds`);
  do not use double-underscore name mangling unless avoiding a real subclass
  collision.
- **Type variables / Protocols**: `PascalCase`, suffix `Protocol` for
  structural types (`SensorReaderProtocol`).

## 2. Test files

- Mirror the `src/` path: `src/foo/bar.py` -> `tests/foo/test_bar.py`.
- Test functions: `test_<unit_under_test>_<behavior_or_condition>`
  (`test_compute_track_covariance_raises_on_singular_matrix`).

## 3. Config files (`configs/`)

- File names: `snake_case.yaml`, named after the component or pipeline stage
  they configure (`tracker.yaml`, `sensor_fusion.yaml`, `hardware_a100.yaml`).
- Keys inside YAML: `snake_case`, matching the parameter names of the
  function/class they are injected into (see Rule 3, no magic numbers, in
  CODING_STANDARDS.md).

## 4. Deployment artifacts (`deployment/`)

- Dockerfiles: `Dockerfile.<service>` (`Dockerfile.tracker`,
  `Dockerfile.inference`).
- Kubernetes manifests: `<service>-<kind>.yaml`
  (`tracker-deployment.yaml`, `tracker-service.yaml`).

## 5. Branches and commits

- Branches: `<type>/<short-description>`, type in
  `{feat, fix, chore, docs, refactor, test}`
  (`feat/multi-target-tracker`, `fix/kalman-divergence`).
- Commit messages: imperative mood, present tense, no trailing period
  (`Add covariance clamping to Kalman update`).

## 6. Prohibited patterns

- No single-letter identifiers outside of tight, obviously-scoped math
  contexts (e.g. `dt`, `x`, `P` in a Kalman filter equation block); never for
  function/class/module names.
- No abbreviations that aren't unambiguous in the radar/tracking domain
  (`cfg` and `dt` are fine; `trk_assoc_calc` is not — prefer
  `track_association_calculator`).
