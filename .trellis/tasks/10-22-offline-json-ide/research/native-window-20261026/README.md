# OHOS window observer and ownership controls

This preparation supersedes readiness611, which was explicitly retired by
channel622 before execution. No SDK, Flutter/Hvigor build, installation or
device command ran in these checks.

The entry is `run_json_ohos_window.ps1`. It sends acceptance and launches the
validation wrapper in one invocation. A retained Windows Job contains the
wrapper and descendants. The wrapper publishes a pending notice only. The
observer waits for actual wrapper exit and an empty Job before relaying
ownership back to the named successor.

Ownership release is independent of runtime acceptance. Failed tests must
release an empty process tree. `handoffReady` records ownership handoff.
`finalGatePassed` records the completed window verdict. The final message
instructs the coordinator to check the completed result, including relay
cleanup and total budget, before starting a successor. No message sent before
the relay exits can prove that relay's final exit.

The total budget includes acceptance, the child wrapper, cleanup and the final
relay. Thirty seconds are reserved after the main wait for current-job
cleanup, relay and local IO. The child receives a smaller remaining budget
and reserves fifty seconds internally. A short window may defer validation
before launch. The frozen proposed command requests 240 seconds.

Five synthetic controls passed: normal completion, a root that leaves a live
owned descendant, child failure, insufficient budget and failed acceptance.
The descendant test records explicit residual cleanup and checks that the
same process identity is gone before relay. Failure/no-launch cases have
`finalGatePassed:false` while their empty ownership trees can be handed back.

`runners/run_json_window_controls.py` creates temporary observer copies. Only
the SDK child and transport bindings change in those copies: a local synthetic
process replaces each. All ownership/wait/cleanup logic uses the actual C#
helper. These fixtures never call a build tool, send a channel message or
contact a device. Their passing result is process-control evidence only.

The independent Pi review recommended retaining resources after a test
failure. That recommendation was rejected: a clean failed validation does
not own a continuing SDK process. Timeout diagnostics and a separate final
window verdict were adopted. The shared lock protecting the Timer callback
and handle close remains unchanged.

The source runtime and prepared isolated app/core are unchanged. A NEW named
serial grant and explicit successor are still required. Neither this
preparation nor the former readiness request is an execution authorization.
