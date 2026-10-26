# Retained Job ownership protocol review

This is a read-only source review. No SDK, compiler, build, runtime control or device command ran.
Only this report was written.

Reviewed byte identities:

- `json-bounded-process.cs`: `6657cffb8a9e4ac741f7143d1d771ae8631c649f9227aa0679a5e0e6e0aa5919`.
- `run_json_ohos_window.ps1`: `aa0af8de601453cb089fc6dcc8cca2a160dac667f08dfafe8221833310fe3df3`.
- `run_json_ohos_release.ps1`: `0db96b75a97d58b2e7ad11eed7243246a402ea74eac3482859b3fdd15fb77e65`.

## Conclusion

A synchronous HOLD loop fixes local handle retention only if its owning process stays alive.
Applied unchanged at both existing levels, it is not sufficient for the literal requirement to
retain every original child/publisher Job until terminal plus active count zero. The outer
validation timer can terminate the child wrapper while that wrapper owns an unresolved nested
phase or publisher Job. Its original handles then disappear with the wrapper. Retaining only the
outer containing Job proves aggregate tree emptiness later, but does not retain the exact nested
Job handles until their own terminal/empty observations.

An outside persistent controller is one solution, but it is not the only solution. A smaller
protocol can keep the present parent invocation alive and treat the validation wrapper as a
custodian rather than a killable payload. The parent must not terminate that custodian at its
own deadline while it may retain nested Job handles. Its own helper must preserve the exact
validation root/Job and enter HOLD while waiting for the custodian to settle. The child can
continue bounded payload termination attempts with its own exact phase/publisher Jobs, and
retain those handles indefinitely on unconfirmed cleanup. This sacrifices a bounded terminal
response on the exceptional HOLD path, which must never be reported as a successful window.

If the existing outer deadline still calls `TerminateJobObject(validationJob, ...)`, strict
nested-handle retention requires another surviving owner of each original nested handle, such
as duplicate handles registered with the parent before the nested payload resumes. Aggregate
parent Job ownership alone is a weaker protocol and needs explicit coordinator acceptance.

## Source evidence

- Helper lines 142-149 install an unconditional Job termination timer.
- Helper lines 162-166 request termination again at the loop deadline.
- Helper cleanup lines 180-208 close the Job and root handles after bounded waits even when
  `TreeEmpty` is false. This is the original defect.
- Window lines 57-62 put the whole child wrapper under that same killable helper.
- Child lines 39 and 149 create nested exact phase and publisher Jobs in the child process.
- Window line 65 checks aggregate validation tree state only after its helper returns.
- Window lines 89-100 correctly separate available relay budget and actual completed verdict.

## Required repair properties

- Preserve original root and Job handles on every uncertain cleanup/error path.
- Check original root handle signal and original Job active count zero before closing either.
- A failed query is unknown. It cannot set empty or close ownership handles.
- Do not infer terminal state from PID existence, an exit-code field or a termination request.
- Dispose or synchronize the termination timer before final closure so it cannot act on a
  closed or reused handle.
- Persist HOLD before a potentially unbounded wait. Include exact root identity and error.
- Do not run a later phase or publisher while an earlier exact Job remains unresolved.
- Protect a child custodian from the enclosing Job timer, or preserve its exact nested handles
  in an owner that survives that timer.
- Keep timeout and cleanup errors in the final failed result even if ownership settles later.
- Recompute actual elapsed time after terminal and relay. A late cleanup is not a <=240-second
  successful window. Missing terminal or missing relay evidence remains HOLD.

## Verification still required

Source review cannot prove actual Windows nested-Job behavior. A fresh authorized controls
window must cover normal exit, descendant cleanup, timeout, forced query/termination failure,
HOLD retention, custodian survival, later recovery and publisher failure. It must observe the
original handles. No native grant should reuse 703 or precede this protocol decision.

## Updated custodian plan review

The updated plan is sufficient for source-level ownership on the managed execution paths.
It does not require an outside controller if the parent invocation remains the surviving
owner and never terminates the resumed child custodian. The live parent still needs its
validation call changed to `RunCustodian`. Acceptance and final publishers remain `Run`.
Do not integrate the candidate without that call-site change.

The candidate reviewed below implements these properties:

- `RunCustodian` delegates to `RunCore(..., true)`.
- Its deadline callback marks `TimedOut` but excludes `TerminateJobObject` for a custodian.
- At the elapsed deadline, the custodian loop publishes HOLD and keeps observing the root.
- Cleanup excludes Job/root termination once a custodian has resumed.
- Normal payload mode retains exact Job-scoped termination attempts.
- Cleanup closes the Job and root only after original root wait signals and original Job
  accounting reports zero. Failed accounting queries reset the observation to unknown.
- A suspended root that failed assignment is terminated by original root handle. Both proof
  conditions still apply before closure.
- Timer disposal waits for the callback before acquiring the cleanup lock, so no callback can
  subsequently act on a closed Job handle. The callback also shares the same lock.
- HOLD sets a non-null error and a sticky `HoldEntered` flag. Cleanup errors remain non-null.
  Timeout stays true. Later ownership recovery therefore cannot become a successful phase.
- The HOLD record names the original owner, root PID/creation FILETIME and retained handles.

A custodian root can become terminal while descendants remain active. The candidate deliberately
keeps that Job in HOLD and does not kill its descendants. This is safe ownership retention, but
may require manual reconciliation if an orphan never exits. It is not a bounded cleanup claim.

An observation exception can replace the textual HOLD reason with another error, but cannot
clear the failure: `HoldEntered` remains set and `Error` remains non-null. Explicitly retaining
both fields in PowerShell rows would improve audit evidence. Call-site checks must reject
`HoldEntered`, `TimedOut`, `CleanupError` or missing terminal/active-zero/closed proof.

The parent must still compute the actual elapsed verdict after relay. A late recovered HOLD
can prove eventual empty ownership, but it cannot pass the 240-second window. A missing relay
or unconfirmed root/Job keeps handoff incomplete.

No runtime behavior was tested. Fresh granted controls remain required before native execution.

Reviewed candidate SHA-256: `2778b1c15c683b8a101a09b8bc444c6163fe2b411a7176f7b38b43106225b2c7` (20635 bytes).

## Integrated live-source review

No blocking issue found in the live integration reviewed below. This is source approval only.
The old initialized manifest is retired and authorizes no execution of these changed bytes.

The parent now passes true only for its validation call at line 67. The owned-call helper
selects `RunCustodian` at lines 31-34. Acceptance and final relay use the default normal mode.
The parent records creation FILETIME, root terminal, Jobactive0, handle closure, HOLD path and
cleanup error. Its successful-row predicate at line 50 rejects HOLD, timeout, cleanup error,
missing terminal proof, missing active-zero proof or unconfirmed handle closure.

The child records the same evidence for ordinary phases, final capture and pending publisher.
Its existing error checks remain fail-closed because the pinned helper makes HOLD and failed
closure produce non-null Error. Directly testing all new fields in child phase predicates would
make this dependency more explicit, but the current pinned source does not admit a false pass.

The parent's final verdict still computes actual elapsed after final relay. A late custodian
cannot pass. The helper cannot return from an unresolved retained HOLD, so parent/child finally
blocks cannot start later publishing while that exact Job remains unconfirmed. A custodian
that exits with live descendants leaves the parent in retained HOLD, as designed.

No old window controls were executed. Their orphan behavior expectations must be adapted for
non-killable custodians. Actual compilation and Windows control behavior remain unproven.

- `json-bounded-process.cs`: 20635 bytes, `2778b1c15c683b8a101a09b8bc444c6163fe2b411a7176f7b38b43106225b2c7`.

- `run_json_ohos_window.ps1`: 10810 bytes, `cd5a80c1812a5b6a6d1c72d94ee8dfb01171e7fd0674acae8dff8303698038ab`.

- `run_json_ohos_release.ps1`: 15632 bytes, `47678ee0df8a5d57d40c8700d98bd1549fe119b88c40764a2035aba6f721e7ab`.

## Synthetic controls pipeline source review

No blocking issue found in the two control scripts reviewed below. The six-file preflight
normalizes required paths before exact key lookup. It verifies file count, byte size and hash
before Add-Type. The validation child alone uses RunCustodian. Acceptance and final relay use
normal Run with strict returned-ownership predicates. The result parser confines child evidence
to the intended directory and requires seven cases plus all ownership/control/final verdicts.
The parent computes the actual total verdict after relay and does not turn expected synthetic
failures into a native acceptance claim.

The seven controls cover normal return, payload timeout, custodian timeout survival, nested
custodian holder survival, missing executable, pre-resume callback failure and nonzero synthetic
publisher. Expected timeout/HOLD cases reject process acceptance while checking recovered
ownership. The child will not launch a later case after unverified returned ownership.

Non-blocking limits:

- These cases do not inject accounting-query failure, termination failure or a permanently
  unresolved payload cleanup. They must not be described as runtime proof of those fault paths.
- The preflight binds six files, but the after-capture identity list omits the two native wrapper
  files that are not executed by this controls pipeline. This is sufficient for the executed
  controls identities. A later native readiness must freshly bind all native runner bytes.
- Preflight rejection occurs before helper compilation. The finally block then attempts a
  helper-based relay, which can fail because the type was never loaded. That path is fail-closed
  and cannot execute validation, but it may need an external retirement notice. It is not an
  automatic successful ownership relay.
- A control may start near the child deadline and finish late. Its completed elapsed verdict
  fails in that case. The script does not promise an unconditional bounded terminal result.

The source-freeze manifest has not been reviewed because it was not generated at this review.
No script, compiler, SDK, runtime control or device action was executed.

- `run_json_retention_window.ps1`: 11815 bytes, `01f5e32396d912d6be6127cf44eb78288f84e6a92c132225c9a10f4018aa0324`.

- `run_json_retention_controls.ps1`: 10785 bytes, `f967c0150f284dc21cf798eb5ff7375de8d9a2f1515a0be30301303927c7d513`.
