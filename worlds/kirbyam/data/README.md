# Kirby & The Amazing Mirror – Canonical Data

These YAML files are the canonical, version-controlled datasets for this world.

- `items.yaml`: item definitions
- `locations.yaml`: location/check definitions
- `goals.yaml`: goals/events definitions

Notes:

- These files should remain stable and reviewable (small diffs, sorted by `key`).
- Addresses are stored per localization (`na`, `eu`, `jp`, `vc`) and may be `null` until verified.
- Prefer adding fields rather than changing meanings of existing fields.

Conventions:

- Keep entries sorted alphabetically by `key`.
- Avoid renaming keys after release; treat keys as stable identifiers.
