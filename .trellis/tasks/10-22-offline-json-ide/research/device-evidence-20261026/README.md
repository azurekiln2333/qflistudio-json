# Offline device-evidence consistency checker

The checker reads evidence captured by a separately authorized device session.
It never invokes a device command, starts a build or accesses the network.

```text
python verify_json_device_evidence.py --hap preserved-harness.hap --artifact harness-artifact.json --process-log process.log --report json_verification_result.json --capture capture.json --output checked.json
python test_json_device_evidence.py
```

The standard-library suite passes 79 synthetic cases. It covers stale reports,
PID/time identity, exact producer status, duplicate keys/markers, wrong types,
failed/running reports, count mismatches, malformed or encrypted ZIP members,
actual compiled bundle/permissions/engine and log/report mismatches. A marker
literal inside a JSON string is not counted as another result. A log-only
`cleanupError` is a mismatch and remains rejected.

The helper recomputes content counters from the three packaged assets.
`runnerPasses == examples` is a required passing-state assertion. it is not a
static measurement of execution. The tool checks actual HAP/kernel/content
hashes against the inspector artifact and rehashes the HAP after reading it.

`capture.json` requires these fields:

```json
{
  "schemaVersion": 1,
  "deviceId": "<assigned target>",
  "platform": "ohos",
  "bundleName": "com.azurekiln.qfli.json",
  "grant": "<actual named device-session grant>",
  "installedHapSha256": "<preserved HAP SHA256>",
  "processId": 12345,
  "startedUtc": "<capture start in UTC>",
  "finishedUtc": "<capture finish in UTC>",
  "processLogSha256": "<raw log SHA256>",
  "reportSha256": "<exported report SHA256>"
}
```

The artifact must be a successful harness inspection, including `inspectedUtc`
and source-dependency evidence. Its inspection precedes the capture window.
The capture window encloses the report window. All timestamps must use the
same UTC clock domain. Report run ID, PID and integer epoch microseconds must
agree. Dart millisecond and microsecond timestamp forms are both accepted.

A wholly historical but internally consistent evidence set can still pass.
The checker does not independently prove installation, hardware origin,
current device assignment or the authority of a supplied grant. It cannot
replace actual retained install/start/export commands and fresh target
observations. An accepted synthetic fixture is never an installed-device pass.

Current limits: HAP512MiB, log16MiB, evidence JSON16MiB, decompressed JSON
members16MiB, streamed ZIP member256MiB and total uncompressed ZIP768MiB.
Failures return exit1 and a failed output. Public API input errors raise
`ValueError` subclasses.

The current catalog derives 340 examples, 340 tutorials, 340 lessons,
440 exercise answers, 340 fixtures and 10 semantic operations. There are
16 tools in the current frozen runtime contract. This derivation is not a
new OHOS run. The pre-identity historical report is rejected by this protocol.
