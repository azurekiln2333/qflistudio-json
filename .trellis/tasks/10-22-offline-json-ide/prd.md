# Complete offline standalone IDE capabilities

## Goal

Make the standalone products useful offline, with the current JSON checkout as the implementation target. Preserve the user's complete request from `C:/Users/lichengyu/.codex/attachments/a5c5fc51-abae-40c5-a792-7d88695907ce/pasted-text-1.txt`; do not equate a JSON-only change with verification of the whole product family.

## Background and authorization

- User explicitly authorizes Trellis planning followed immediately by implementation, parallel workers, conventional commits and pushing when possible. The later “继续” confirms continuation. No additional planning approval is required.
- This independent Flutter repository depends on `../qfli_studio_core`. Core is a separate Git repository shared by sibling products.
- Initial uncommitted OHOS agreement/signing changes, LICENSE and generated desktop registrants belong to the existing worktree. Preserve and exclude them from task commits.
- This checkout has no Git remote. Core has multiple named remotes. Never infer a product remote from core remotes.

## Requirements and acceptance evidence

| ID | User requirement | Observable acceptance / authoritative evidence |
| --- | --- | --- |
| R1 | Follow Trellis, plan first, coordinate workers | PRD, design, implementation plan, curated context, task state, review and journal exist; worker ownership documented. |
| R2 | Check every existing example on current OHOS tooling | Enumerate every JSON example and tutorial code/exercise, validate all with the shipped implementation, build OHOS asset bundle, record tool versions and actual target-device evidence separately. No desktop-only test is called a device pass. |
| R3 | Add considerably more than 100 useful, tested examples | At least 200 new distinct, explained JSON examples; unique IDs/code; fixtures and expected output validated; all assets accessible from the local repository and importable. |
| R4 | Tutorial/example language filters and title badges | Shared pages expose language filter when multiple languages apply and show the actual language near titles; JSON product stays JSON-only. Widget tests cover filtering and badges. |
| R5 | Useful language tools directly in tools tab | JSON-specific operations are separate cards in the existing tools grid, with working offline transformations/validation and tests; no intermediate product feature hub. |
| R6 | Editor checking, squiggles, location and diagnostics panels | JSON syntax errors expose line/column, highlight the error, and let users navigate; correcting input clears errors; JSON run validates and prints actual output. |
| R7 | File tree expansion state | Close/reopen sidebar and reconstruct explorer without losing expansion; rapid project changes cannot restore another project's state; persistence does not overwrite unrelated history fields. Regression tests. |
| R8 | Investigate workspaces/multiple projects | Inspect and test existing project switching; add useful local workspace behavior without discarding existing project data or rewriting other products' state. |
| R9 | Debug, logs, Problems/Output/Debug Console/Terminal/Ports where possible | JSON has no executable debugger. Provide meaningful validation/problems/output and local terminal commands; avoid pretend breakpoints, debug sessions, or network ports. Record executable-language debugging as separately unverified family work. |
| R10 | Standalone must remain offline | New code performs no network requests; local schema references never fetch URLs; remove network permissions/online entry points from JSON host where safe while preserving existing agreement work. Test offline profile and host boundary. |
| R11 | Syntax highlighting and C/C++ headers | Verify JSON highlighting/import/editor behavior here; record C/C++ header/toolchain checks as family requirements not proven by this checkout. |
| R12 | Python modules/pip in sandbox | Preserve this family requirement; this JSON app must not add pip/network behavior. Inspection of sibling Python capabilities is separate from proof of their OHOS runtime. |
| R13 | Research current VS Code/JetBrains tools | Consult official primary documentation; record useful offline JSON features and chosen supported contracts. |
| R14 | Standard commits and push when possible | Commit only reviewed task-owned files with conventional messages; record hashes, remaining user changes, configured remotes and actual push result/reason unavailable. |

## Product boundary

JSON is a data format; its runnable outcome is parsing, validation, formatting and navigation. Schema support must state its supported subset and report unsupported keywords instead of silently accepting them. Shared editor fixes can benefit other products, but their runtime correctness requires their own evidence. The parent remains open while any required evidence is missing.

## Known external gates

- The initial missing-device gate was resolved on 2026-10-22: an API 26 x86_64 emulator is attached. The installed harness passes every JSON catalog runner; final-package and ordinary-UI evidence is recorded separately in `research/ohos.md`.
- Three configured signing files do not exist. Hvigor's `properties.enableSignTask=false` builds an unsigned HAP successfully, and the attached emulator accepts it. Signed release distribution remains unverified.
- Product repository has no remote, so a push cannot be performed without an authoritative destination.
