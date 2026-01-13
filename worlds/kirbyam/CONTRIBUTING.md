# Contributing

Thank you for your interest in contributing to the **Kirby & The Amazing Mirror** Archipelago world.

This project follows the **standards, expectations, and development model of the Archipelago project**.  
Contributors are expected to be familiar with Archipelago’s core documentation.

---

## Scope of Contributions

Contributions may include (but are not limited to):

- World logic (regions, items, locations, rules)
- Tests and validation improvements
- Client-side BizHawk/Lua enhancements
- Tracker support (Universal Tracker / PopTracker)
- Documentation and guides
- Bug fixes and refactors

If you are unsure whether a change is appropriate, please open an issue first.

---

## Canonical References (Required Reading)

Before contributing, please review the following **Archipelago documentation**:

- **Contributing Guidelines**  
  <https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/contributing.md>

- **Adding Games to Archipelago**  
  <https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/adding%20games.md>

- **World API Documentation**  
  <https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/world%20api.md>

- **Style Guide**  
  <https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/style.md>

- **Testing Documentation**  
  <https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/tests.md>

- **APWorld Developer FAQ**  
  <https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/apworld_dev_faq.md>

This repository intentionally mirrors Archipelago’s conventions rather than redefining them.

---

## Code Style

- Python code **must** follow Archipelago’s style guide:
  - PEP8-based
  - 120 character line limit
  - Double-quoted strings
  - Type annotations where reasonable
- Keep formatting consistent within files and modules
- Avoid unnecessary stylistic refactors mixed with functional changes

Refer to:
<https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/style.md>

---

## Tests (Strongly Expected)

All logic changes **should include tests**.

- World logic tests live under: `worlds/kamirror/test`
- Prefer tests based on `WorldTestBase`
- Ensure:
- All locations are reachable with full inventory
- At least one location is reachable from an empty state
- Generation does not error under supported options

Relevant documentation:
<https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/tests.md>

Pull requests that introduce regressions or lack coverage for critical logic changes may be rejected.

---

## Commits and Pull Requests

- Keep commits focused and logically scoped
- Avoid bundling unrelated changes
- When opening a PR, clearly describe:
- What was changed
- Why the change was made
- How it was tested (manual and/or automated)

If your PR affects logic in non-obvious ways, please explain the reasoning.

---

## ROMs and Assets

Do **not** submit:

- ROMs
- Decompiled game code
- Copyrighted assets

This project contains only original code and metadata.

---

## Communication

Development discussion primarily happens via:

- GitHub Issues and Pull Requests
- Archipelago Discord (world development channels)

A dedicated Discord channel for this world will be created once the project reaches a stable POC.

---

## License

By contributing, you agree that your contributions are licensed under the **MIT License**, consistent with this repository.

Thank you for helping improve the Kirby & The Amazing Mirror Archipelago world.
