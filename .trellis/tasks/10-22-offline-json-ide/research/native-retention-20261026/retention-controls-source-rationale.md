# Job-retention controls: source rationale

The controls runner is `.trellis/.runtime/run_json_retention_controls.ps1`.
It is authored but unexecuted. No Add-Type, C# compiler, SDK, Flutter, build or device command
ran during preparation. The script contains compilation solely for a future granted run.
The failed first file-writing shell command parsed no task script and created no processes.

Run only under a fresh actual host-controls grant. The original tool invocation must be the
surviving owner, outside any enclosing killable validation Job. Never place a subprocess timeout
around it. It targets 60 seconds total. A later case is not launched after this start budget.
Unresolved exact ownership stays LIVE HOLD inside the helper. It cannot be killed to force a
nominal total bound. A late completed result fails the actual 60-second budget.

The seven cases run serially. Normal exit requires a completion marker and accepted exit0.
Payload timeout requires an entered marker, a failed exit and no completion marker. Custodian
timeout requires exit0 and a completion marker after the deadline, but rejects acceptance due
to sticky timeout/HOLD. It verifies the HOLD sidecar and exact root creation FILETIME.
Nested-holder creates a child that loads the same helper, runs a separate inner payload and
writes the inner full result only after it observes terminal+active0. The enclosing custodian
has a shorter deadline. Its survival, both completion markers and both exact root identities
prove the parent did not terminate that nested-handle owner at its deadline.
Invalid executable must create no root and return an error. A throwing onStarted callback must
leave the root unresumed and clean its exact assigned Job; no child marker may appear.
A synthetic publisher exits9 and writes a marker. It performs no real channel or network call.

Each returned row requires RootTerminal, JobActiveZero, TreeEmpty and HandlesClosed. A created
root requires a positive original-handle creation FILETIME. An unverified returned row aborts
before another case. Every full ProcessResult is retained. Expected failed payloads can pass a
control but their processAccepted remains false. HOLD can never become processAccepted.
The final summary records exact script/helper/PowerShell hashes, verifies those identities again,
retains per-case script hashes, elapsed times and full results, and requires all seven controls.

The runner does not inject fake accounting or termination failures. It makes no claim to prove
all Windows API failure paths. Such paths retain source-level review until a separate meaningful
isolated fault-injection design is authorized.

Command template (the integer must come from the returned actual channel grant):

```text
D:/ProgramFiles/PowerShell/7/pwsh.exe -NoProfile -NonInteractive -File D:/MyNewProjects/qfli_json/.trellis/.runtime/run_json_retention_controls.ps1 -GrantEvent <NEW-ACTUAL-CONTROLS-GRANT> -MaxSeconds 60
```

The script itself sends no ACK or final channel message. The primary owner must bind its
surrounding acceptance/actual-terminal/final relay protocol under the new controls grant.
A controls pass does not authorize a native build or any device action.
