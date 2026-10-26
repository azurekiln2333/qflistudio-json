# Native retry readiness, 2026-10-26

This source-only repair prepares a fresh unsigned x64 harness and normal package window. No new
native grant has been received or consumed. Grant 703 remains a failed, terminally released
window. No device action ran.

The inspector now accepts only the declared isolated native plugin inputs. It binds the source
capture identity, metadata mappings, package configuration, compiler inputs and aggregate
depfile. It rejects live roots, other staging roots and links escaping the isolated roots.
External SDK and Pub inputs are not a complete supply-chain binding.

The child captures inputs with `--expected-prepared` before SDK execution. It compares the
reviewed roots, source files, cache references, tools, runner identities, build commands and
frozen core identity. Any mismatch fails before the SDK starts. The after-capture still compares
raw file bytes. No lock exclusion or normalization was added.

The initialized snapshot contains 805 files and seven cache references. It contains prior build
intermediates from failed grant 703. It is not a clean build. The original manifest maps equal
the committed 703 before-capture. The initialized maps equal the committed 703 after-capture.
The historical delta is one generated file, four lock files and one cache reference. This
provenance never permits a future build to ignore changes.

The prepared manifest SHA-256 is
`9d6f867610ed217cc974382a427279c6982c0ed92bd0b0571bae3e30ae4ba62a`. Its frozen shared core
remains `2f9039a3ba95449679b17257b0313c1ee3644a2c`. This does not establish equality with
current shared-core work in progress.

Validation: 19 source-attribution controls and 16 readiness controls passed using the archived
scripts. Six source-only CLI cases returned their expected exits. These include rejected tool
and source hash changes. Three PowerShell files parsed without errors. The final inspector also
passed an offline diagnostic inspection of the preserved 703 harness HAP. That diagnostic result
does not retroactively pass grant 703 and does not prove normal-package or device acceptance.

`validation.json` records exact archive bytes and hashes. `before.json`, `after.json` and
`guarded.json` retain full captured maps. `capture-checks.json` records negative controls and
local raw evidence identities. `command-template.json` is an unauthorized template requiring a
new actual integer channel grant. The unchanged parent observer retains acceptance, child
waiting and final ownership relay in one invocation with a 240-second total limit. Unknown
terminal ownership remains HOLD. Validation failure is never a pass.

Current-source device acceptance, signing, ARM64 and all-family acceptance remain open. No
shared-core files were changed by this repair.

## Retention issue found before READY

Root review found that the unchanged bounded Job helper closes handles when cleanup remains
unconfirmed. This violates the retained-HOLD requirement. This archive is source-only repair
evidence and is NOT READY for execution. The command template grants no execution authority.
A separate retention repair and validation must precede any fresh native grant request.
