# Exact Job retention: source-only candidate

Status: source candidate only. No compiler, SDK, Flutter, build or device command ran.
The live helper and wrappers remain unchanged. The candidate is not installed.

## Original blocking defect

The live `json-bounded-process.cs` closes its exact Job after a five-second cleanup wait even
when accounting is nonzero or unavailable. It closes the root handle when terminal wait fails.
An error flag prevents a pass but does not preserve recoverable original-object ownership.
Closing the last kill-on-close Job handle requests termination. It does not prove active0.

## Candidate API

`json-bounded-process-retained.cs` retains the existing `Run` signature for payloads and adds
`RunCustodian` with the same arguments for an owner of nested Job handles. Both route through
one implementation. Both keep original Job, root and thread handles until independently
observed root terminal and Jobactive0. Failed accounting means unknown. A failed-to-assign
suspended root must still become terminal before closure.

Payload `Run` may terminate only its own exact Job/root at the deadline. Unconfirmed cleanup
enters HOLD after five seconds and retains the originals while it continues observing them.
It cannot return while ownership is unknown.

`RunCustodian` marks timeout but never terminates a successfully resumed custodian or its
containing Job. At the deadline it persists HOLD and continues observing the original root and
Job. Cleanup likewise never kills the resumed custodian. A never-resumed suspended root can be
terminated because it could not have created nested owners. After a timeout or HOLD settles,
the result remains failed. It cannot turn into a successful window.

The timer is disposed and its callback completion is awaited before handle closure. A callback
cannot race a closed/reused handle. Every uncertain cleanup path retains exact handles.

## Required wrapper integration

Only the parent's validation-wrapper call must use `RunCustodian`. Acceptance and final relay
publishers remain ordinary payload `Run`. The child keeps payload `Run` for build phases,
source captures and its pending publisher. That child cannot return from a payload call until
that exact payload's root and Job are terminal/active0. The parent cannot kill this child while
it is preserving nested handles. The original top-level tool invocation must stay alive on
HOLD. Do not terminate that invocation to force a nominal deadline or retry the grant.

This eliminates the earlier nested-parent blocker without an external controller or handle
duplication. That conclusion depends on using the custodian overload at the enclosing
validation call. Installing the cleanup loop alone remains insufficient.

## Durable HOLD observation

Before an unbounded HOLD wait, the candidate writes `<stderr>.ownership-hold.json` with
status HOLD, pass false, terminal false, owner PID, exact root PID and creation FILETIME,
local original Job/root handle values, mode, UTC and error. It flushes the file to disk.
It also emits the same record on stderr. A persistence error remains a cleanup error and
never causes handle closure. The sidecar records HOLD entry, not a final release receipt.
The final enclosing result must establish actual termination and all Jobactive0 observations.

## Budget and acceptance

The execution deadline and a successful total-window budget are distinct. Ordinary success
can finish within 240 seconds. Exceptional HOLD may exceed that bound to preserve ownership.
Such a run must remain failed and must never claim a <=240-second successful handoff. The
completed outer result must include actual elapsed time after final relay. No missing terminal
or relay can be called a pass. The original grant703 remains consumed.

## Review and validation limits

The candidate follows the smaller custodian protocol described in
`retention-protocol-review.md`. Source checks confirm the unconditional closure block is gone,
the custodian branches never issue termination after resume, and closure follows the combined
root-terminal/Jobactive0 proof. Root creation FILETIME comes from the retained process handle.
No C# syntax or Windows behavior was executed. A fresh controls grant must verify normal exit,
descendant cleanup, timeout, failed assignment, failed accounting/termination, HOLD retention,
custodian survival, later recovery and publisher failure before native acceptance.
