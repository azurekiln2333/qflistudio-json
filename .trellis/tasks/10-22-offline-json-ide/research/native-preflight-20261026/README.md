# Isolated OHOS native preflight

October 26, 2026: source-only preparation is ready for a new named execution
window. No SDK, Hvigor, Flutter build, package installation or device command
ran in this preflight. The family task remains in progress.

The five runner references preserve the exact local bytes recorded in
`preflight.json`. The live entry is
`.trellis/.runtime/run_json_ohos_release.ps1`; the retained references do not
change the source snapshot or the application. The snapshot still uses the
published core `2f9039a3ba95449679b17257b0313c1ee3644a2c` and the JSON runtime
covered by the October 24 host result.

Both captures cover 804 input files, six cache references and all eight
TypeScript/JSON sources of the installed Flutter Hvigor plugin. The unchanged
comparison exits 0. Adding a named tool identity exits 1. A missing-Python
negative control exits 1, persists a failed result and starts neither work
phases nor a publisher. PowerShell AST and Python source parsing pass.

The wrapper guards prerequisite and publication failures, records unknown
process ownership conservatively, compares all captured categories through
`--before`, and records per-phase elapsed time. It reserves 50 seconds for
current-job cleanup, final capture and publication. Actual budget overrun
fails the run. Publication errors mark the release text unconfirmed. Failed
final persistence emits a failed JSON record on stderr and requires the outer
exit status for acceptance.

The independent Pi review also suggested a Timer handle race. Inspection
rejects that finding: both the timer callback and final handle close hold
the same lock. A callback before close finishes before the lock transfers;
a callback after close observes the zero handle. No process helper change
was needed.

The modes still build sequentially in one fresh isolated native root. The
inspector preserves each package before the next build, requires distinct
kernel hashes and verifies compiler plus aggregate dependency files. This
is source-bound unsigned-package inspection, not proof that either entry
runs on a device. Full SDK and Java installation bytes are outside this
capture scope.

The private ignored native snapshot retains embedded build-profile signing
configuration. Known standalone credential files are excluded. Only paths
and hashes enter capture evidence; raw build-profile contents are not
exported into this directory. Signing remains disabled for the planned
unsigned build.

A real run still requires a fresh named serial grant, a frozen command and
an explicit successor. Do all preparation before accepting that window.
Installed-target, signed-distribution and physical ARM64 acceptance remain
separate unfinished requirements.
