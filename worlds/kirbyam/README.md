# Archipelago – Kirby & The Amazing Mirror (GBA) World

Archipelago multiworld support for **Kirby & The Amazing Mirror** using **BizHawk** as the emulator/client runtime.

This repository contains the **world implementation** (generation, items/locations, logic, options, documentation) and
client-side components needed to play Kirby & The Amazing Mirror in Archipelago.

## Project Status

**Current status:** Early development (starting from scratch).  
**Target:** Rapid Proof of Concept (POC), then iterative expansion.

### Initial Scope

- **North American ROM only** (other localizations planned later)
- **BizHawk**-based client integration
- High emphasis on **logging** and **tests** from the beginning

### Long-Term Goals

- Multi-localization support (EU/JP and others after NA)
- Tracker integration (Universal Tracker + PopTracker)
- In-game notifications for item send/receive
- Room/entrance randomization (phased)
- Lobby randomization (phased)
- Mini-boss / boss randomization (phased)
- Ability-source randomization (phased)
- Traps (phased)
- Ability gating behind checks / progression logic improvements (phased)
- Optional Ability Room handling (phased)
- Optional Master Sword handling (phased)
- DeathLink support (phased)

## What’s in This Repo

Typical structure (may evolve as implementation grows):

- `worlds/kirbyam/` – Archipelago world package (Python)
  - `__init__.py` – World entrypoint
  - `items.py`, `locations.py`, `regions.py`, `rules.py`, `options.py` – modular world code
  - `docs/` – world docs rendered by WebHost
  - `data/` – data used to create the logic
  - `test/` – unit tests for logic and edge cases
  - `requirements.txt` – world-specific dependencies (if needed)
- `client/` (optional, if kept here) – BizHawk Lua client scripts and support files
- `tools/` (optional) – data generation, tracker export tools, ROM table tooling, etc.

## Roadmap, Bugs, and Feature Requests

This project uses GitHub Issues and Projects for planning and tracking.

- **Public roadmap:** GitHub Projects (once public / if already public)
- **Issue reporting:** GitHub Issues (`bug` label)
- **Feature requests:** GitHub Issues (`feature request` label)

If the repo is still private, these will become visible when the repo transitions public.

## Development Milestones

High-level plan:

1. **Phase 0 – Setup**
   - Local dev environment + Archipelago fork workflow
   - World skeleton and test harness

2. **Phase 1 – POC (fast)**
   - Minimal world: 1 region, a handful of items/locations
   - Valid generation + basic test coverage
   - Establish logging conventions

3. **Phase 2 – Core World**
   - Full location list, item pool, and progression logic
   - Stable generation, logic tests, and documentation

4. **Phase 3+ – Feature Expansion**
   - Trackers, notifications, DeathLink, shuffles, traps, multi-localization, etc.

## Emulator / Client Plan (BizHawk)

The intended play environment is:

- **BizHawk** for emulation
- A **Lua client** that connects to the Archipelago server, reports location checks, and applies received items

Client-side work will be introduced incrementally:

- Early phases focus on world generation + logic correctness
- Client integration becomes a focus after stable core logic

## Localization Plan

The project will:

1. Start with **North American** Kirby & The Amazing Mirror
2. Add additional localizations later via a structured approach:
   - Per-ROM memory maps / offsets
   - Version detection in the client (where applicable)
   - Shared canonical item/location naming across versions

## Trackers (Universal Tracker + PopTracker)

The tracker plan is:

- **Fork** and integrate with Universal Tracker and PopTracker
- Maintain a single canonical dataset (items/locations/flags) and export to tracker formats where feasible

## Logging and Testing

### Logging

Expect verbose logging across:

- Generation stages (regions, rules, itempool, output)
- Client communications (connect, resync, send/receive, special features)

### Tests

This world will include unit tests following Archipelago’s world testing conventions:

- Use `WorldTestBase`-based tests for logic and regression coverage
- Keep tests fast and targeted

## Contributing

Contributions are welcome once the repo is public and the POC is working.

This project adheres to the Archipelago contribution expectations:

- Follow Archipelago style guidance (including line length, quoting, typing)
- Include tests for critical logic changes
- Avoid introducing test regressions across supported Python versions

See:
- `CONTRIBUTING.md` (in this repo)
- Archipelago core contributing guidance and style/testing docs (referenced from CONTRIBUTING.md)

## Discord

A dedicated channel in the Archipelago Discord will be created once the POC is playable/demonstrable.  
Until then, development discussion can happen in the general AP world-dev channels.

## License

This project is licensed under the **MIT License**.

See the `LICENSE` file for full license text.

### Legal Notice

This repository contains **no ROMs, no copyrighted game assets**, and no proprietary Nintendo or HAL Laboratory source code.

**Kirby & The Amazing Mirror** is © Nintendo / HAL Laboratory.  
You must provide your own legally obtained game copy to play.

This project is a fan-made interoperability and randomization tool and is not affiliated with or endorsed by Nintendo or HAL Laboratory.
