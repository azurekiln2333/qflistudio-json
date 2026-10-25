"""Synthetic offline tests for ``verify_json_device_evidence.py``.

Every fixture here is generated in a temporary directory from pure Python
standard-library code. No test builds, installs, flashes, or contacts a device.
A passing run shows only that the checker accepts consistent synthetic input
and rejects specific tampered input. It never proves that a real HAP was
installed, that a real device produced the report, or that an authorization is
genuine. A synthetic fixture must never be presented as device evidence.

The fixtures follow ``device-evidence-protocol-review.md``: lowercase report
status (``running`` / ``passed`` / ``failed``) versus uppercase artifact status
(``PASS`` / ``FAIL`` / ``BLOCKED``), millisecond-or-microsecond timestamps,
per-branch semantic counting, strict log-versus-report text equality, and the
progress marker that shares a prefix with the result marker.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
import struct

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "verify_json_device_evidence.py"

BUNDLE = "com.azurekiln.qfli.json"
PERMISSION = "ohos.permission.READ_PASTEBOARD"
KERNEL_ENTRY = "resources/rawfile/flutter_assets/kernel_blob.bin"
LIB_ENTRY = "libs/x86_64/libflutter.so"
CONTENT_ENTRY = {
    "examples.json": "resources/rawfile/flutter_assets/assets/content/examples.json",
    "tutorials.json": "resources/rawfile/flutter_assets/assets/content/tutorials.json",
    "catalog_audit.json": "resources/rawfile/flutter_assets/assets/content/catalog_audit.json",
}

TOOLS_CONTRACT = 16
MIN_ENTRIES = 320
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
PROGRESS_LINE = "QFLI_JSON_VERIFY_PROGRESS running 0/340"


def _load_module():
    if not MODULE_PATH.is_file():
        return None
    spec = importlib.util.spec_from_file_location("verify_json_device_evidence_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = _load_module()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def stamp(moment: datetime) -> str:
    """Format a UTC moment like Dart ``toUtc().toIso8601String()``."""
    return moment.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def micros(moment: datetime) -> int:
    return (moment - EPOCH) // timedelta(microseconds=1)


def _dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, indent=2)


def _compact(value) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def _find_result_lines(text: str) -> list:
    marker = "QFLI_JSON_VERIFY_RESULT "
    return [line for line in text.splitlines() if marker in line]


def _result_payload(line: str) -> str:
    return line.split("QFLI_JSON_VERIFY_RESULT ", 1)[1]


# --------------------------------------------------------------------------
# Content builders. The shapes mirror the real bundled assets so any parser
# that accepts the shipped curriculum also accepts these fixtures.
# --------------------------------------------------------------------------


def _example_entry(index: int, semantic: str) -> dict:
    if semantic == "patch":
        payload = {
            "document": {"name": f"note-{index:03d}"},
            "operations": [{"op": "add", "path": "/archived", "value": False}],
            "expected": {"name": f"note-{index:03d}", "archived": False},
        }
    elif semantic == "merge":
        payload = {
            "target": {"name": f"note-{index:03d}", "value": 1},
            "patch": {"value": 2},
            "expected": {"name": f"note-{index:03d}", "value": 2},
        }
    elif semantic == "both":
        payload = {
            "document": {"name": f"note-{index:03d}"},
            "operations": [{"op": "add", "path": "/archived", "value": False}],
            "target": {"value": 1},
            "patch": {"value": 2},
            "expected": {"name": f"note-{index:03d}", "archived": False},
        }
    else:
        payload = {"schemaVersion": 1, "index": index, "values": [index, index + 1]}
    code = _dumps(payload)
    return {
        "id": f"json-example-{index:03d}",
        "language": "json",
        "type": "json",
        "locale": "zh-CN",
        "level": "beginner",
        "title": f"JSON example {index:03d}",
        "summary": "Synthetic offline fixture entry.",
        "concepts": ["fixture"],
        "source": "synthetic offline fixture",
        "license": "test fixture",
        "updatedAt": "2026-10-22",
        "code": code,
        "expectedOutput": code,
        "inputFixtures": {"data.json": code},
        "templateType": "json",
        "sourceLessonId": f"json-tutorial-{index:03d}-lesson",
    }


def _tutorial_entry(index: int, exercises: int) -> dict:
    code = _dumps({"schemaVersion": 1, "index": index})
    lesson = {
        "id": f"json-tutorial-{index:03d}-lesson",
        "title": f"Lesson {index:03d}",
        "summary": "Synthetic offline fixture lesson.",
        "concepts": ["fixture"],
        "explain": "Synthetic offline fixture explanation.",
        "code": code,
        "output": code,
        "exercises": [
            {
                "prompt": f"Exercise {index:03d}-{slot}",
                "hint": "fixture",
                "answer": _dumps({"explanation": "fixture"}),
            }
            for slot in range(exercises)
        ],
    }
    return {
        "id": f"json-tutorial-{index:03d}",
        "language": "json",
        "type": "json",
        "locale": "zh-CN",
        "level": "beginner",
        "title": f"JSON tutorial {index:03d}",
        "summary": "Synthetic offline fixture tutorial.",
        "concepts": ["fixture"],
        "source": "synthetic offline fixture",
        "license": "test fixture",
        "updatedAt": "2026-10-22",
        "lessons": [lesson],
    }


def _exercise_counts(n_tutorials: int, total_exercises: int) -> list:
    doubled = total_exercises - n_tutorials
    return [2 if index < doubled else 1 for index in range(n_tutorials)]


def derive_metrics(examples_data: dict, tutorials_data: dict) -> dict:
    """Recompute the report metrics from the packaged curriculum.

    ``semanticOperations`` accumulates once per matching branch, so one example
    that carries both the patch and the merge shapes adds two.
    """
    examples = examples_data["entries"]
    tutorials = tutorials_data["entries"]
    lessons = [lesson for tutorial in tutorials for lesson in tutorial.get("lessons", [])]
    semantic = 0
    for entry in examples:
        try:
            value = json.loads(entry["code"])
        except (KeyError, TypeError, ValueError):
            continue
        if not isinstance(value, dict):
            continue
        if "operations" in value and "expected" in value:
            semantic += 1
        if "target" in value and "patch" in value and "expected" in value:
            semantic += 1
    return {
        "examples": len(examples),
        "runnerPasses": len(examples),
        "tutorials": len(tutorials),
        "lessons": len(lessons),
        "exerciseAnswers": sum(len(lesson.get("exercises", [])) for lesson in lessons),
        "fixtures": sum(len(entry.get("inputFixtures", {})) for entry in examples),
        "semanticOperations": semantic,
        "tools": TOOLS_CONTRACT,
    }


class Fixture:
    """Build one consistent set of synthetic evidence files."""

    def __init__(
        self,
        directory: Path,
        *,
        n_examples: int = 340,
        n_tutorials: int = 340,
        total_exercises: int = 440,
        n_patch: int = 7,
        n_merge: int = 3,
        n_both: int = 0,
    ) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.hap = self.dir / "entry-default-unsigned.hap"
        self.artifact_path = self.dir / "artifact.json"
        self.log_path = self.dir / "process.log"
        self.report_path = self.dir / "report.json"
        self.capture_path = self.dir / "capture.json"

        self.n_examples = n_examples
        self.n_tutorials = n_tutorials
        self.total_exercises = total_exercises

        self.start = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
        self.finish = self.start + timedelta(seconds=5)
        self.pid = 5271
        self.kernel = b"kernel-blob-fixture-0000"
        self.lib = b"\x7fELF synthetic fixture payload"
        self.module = {
            "app": {"bundleName": BUNDLE},
            "module": {
                "requestPermissions": [
                    {"name": PERMISSION, "reason": "$string:pasteboard_reason"}
                ]
            },
        }

        def semantic_mode(index: int) -> str:
            if index < n_patch:
                return "patch"
            if index < n_patch + n_merge:
                return "merge"
            if index < n_patch + n_merge + n_both:
                return "both"
            return "none"

        self.examples_data = {
            "schemaVersion": 1,
            "entries": [
                _example_entry(index, semantic_mode(index)) for index in range(n_examples)
            ],
        }
        self.tutorials_data = {
            "schemaVersion": 1,
            "entries": [
                _tutorial_entry(index, exercises)
                for index, exercises in enumerate(
                    _exercise_counts(n_tutorials, total_exercises)
                )
            ],
        }
        counts = derive_metrics(self.examples_data, self.tutorials_data)
        self.audit_data = {
            "schemaVersion": 1,
            "totalExamples": counts["examples"],
            "totalTutorials": counts["tutorials"],
        }
        self.metrics = counts

        self.report = {}
        self.artifact = {}
        self.capture = {}

        self._write_hap()
        self._write_report(self._base_report())
        self._write_log()
        self._write_artifact()
        self._write_capture()

    # -- serialization ---------------------------------------------------

    def _content_bytes(self) -> dict:
        return {
            "examples.json": (_dumps(self.examples_data) + "\n").encode("utf-8"),
            "tutorials.json": (_dumps(self.tutorials_data) + "\n").encode("utf-8"),
            "catalog_audit.json": (_dumps(self.audit_data) + "\n").encode("utf-8"),
        }

    def _write_hap(self) -> None:
        content = self._content_bytes()
        with zipfile.ZipFile(self.hap, "w", zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr("module.json", _dumps(self.module))
            bundle.writestr(LIB_ENTRY, self.lib)
            bundle.writestr(KERNEL_ENTRY, self.kernel)
            for name, entry_path in CONTENT_ENTRY.items():
                bundle.writestr(entry_path, content[name])

    # -- report / log ----------------------------------------------------

    def _base_report(self) -> dict:
        report = dict(self.metrics)
        report.update(
            {
                "passed": True,
                "platform": "ohos",
                "failures": [],
                "runId": f"{self.pid}-{micros(self.start)}-0",
                "startedUtc": stamp(self.start),
                "finishedUtc": stamp(self.finish),
                "status": "passed",
            }
        )
        return report

    def _write_report(self, data=None) -> None:
        if data is not None:
            self.report = dict(data)
        self.report_path.write_text(_dumps(self.report) + "\n", encoding="utf-8")

    def _log_line(self, data) -> str:
        return "QFLI_JSON_VERIFY_RESULT " + _compact(data)

    def _write_log(self, text=None) -> None:
        if text is None:
            text = PROGRESS_LINE + "\n" + self._log_line(self.report) + "\n"
        self.log_path.write_text(text, encoding="utf-8")

    # -- artifact --------------------------------------------------------

    def _write_artifact(self, **overrides) -> None:
        with zipfile.ZipFile(self.hap) as bundle:
            entries = {}
            for info in bundle.infolist():
                if info.is_dir():
                    continue
                data = bundle.read(info.filename)
                entries[info.filename] = {"bytes": len(data), "sha256": sha256_bytes(data)}
            assets = {}
            for name, entry_path in CONTENT_ENTRY.items():
                data = bundle.read(entry_path)
                assets[name] = {
                    "entry": entry_path,
                    "bytes": len(data),
                    "sha256": sha256_bytes(data),
                }
            module = json.loads(bundle.read("module.json").decode("utf-8"))
        payload = {
            "passed": True,
            "status": "PASS",
            "inspectedUtc": stamp(self.start - timedelta(seconds=120)),
            "mode": "harness",
            "hap": str(self.hap),
            "hapSha256": sha256_file(self.hap),
            "copiedHap": None,
            "bundleName": module["app"]["bundleName"],
            "permissions": [item["name"] for item in module["module"]["requestPermissions"]],
            "kernelSha256": entries[KERNEL_ENTRY]["sha256"],
            "entries": entries,
            "contentAssets": assets,
            "sourceDependencies": {
                "status": "PASS",
                "sources": {
                    "app": [{"path": "app/lib/main.dart", "sha256": "0" * 64}],
                    "core": [{"path": "core/lib/services/studio_profile.dart", "sha256": "1" * 64}],
                    "re_editor": [{"path": "re_editor/lib/re_editor.dart", "sha256": "2" * 64}],
                },
            },
        }
        payload.update(overrides)
        self.artifact = payload
        self.artifact_path.write_text(_dumps(payload) + "\n", encoding="utf-8")

    def drop_artifact_key(self, key: str) -> None:
        payload = dict(self.artifact)
        payload.pop(key)
        self.artifact = payload
        self.artifact_path.write_text(_dumps(payload) + "\n", encoding="utf-8")

    # -- capture ---------------------------------------------------------

    def _write_capture(self, **overrides) -> None:
        payload = {
            "schemaVersion": 1,
            "deviceId": "emulator-5554",
            "platform": "ohos",
            "bundleName": BUNDLE,
            "grant": "SYNTHETIC-NAMED-GRANT-777",
            "installedHapSha256": sha256_file(self.hap),
            "processId": self.pid,
            "startedUtc": stamp(self.start - timedelta(seconds=60)),
            "finishedUtc": stamp(self.finish + timedelta(seconds=60)),
            "processLogSha256": sha256_file(self.log_path),
            "reportSha256": sha256_file(self.report_path),
        }
        payload.update(overrides)
        self.capture = payload
        self.capture_path.write_text(_dumps(payload) + "\n", encoding="utf-8")

    # -- targeted mutations ----------------------------------------------

    def set_report(self, **overrides) -> None:
        """Change the report and keep the log and capture consistent with it."""
        data = dict(self.report)
        data.update(overrides)
        self._write_report(data)
        self._write_log()
        self._write_capture()

    def set_log_field(self, **overrides) -> None:
        """Change only the log payload, so log and report disagree on those keys."""
        data = dict(self.report)
        data.update(overrides)
        self._write_log(PROGRESS_LINE + "\n" + self._log_line(data) + "\n")
        self._write_capture()

    def duplicate_marker(self) -> None:
        self._write_log(self._log_line(self.report) + "\n" + self._log_line(self.report) + "\n")
        self._write_capture()

    def use_millisecond_timestamps(self) -> None:
        """Trim the report and capture starts to Dart's 3-digit millisecond form."""

        def trim(moment: datetime) -> str:
            return stamp(moment)[:23] + "Z"

        data = dict(self.report)
        data["startedUtc"] = trim(self.start)
        data["finishedUtc"] = trim(self.finish)
        self._write_report(data)
        self._write_log()
        self._write_capture(
            startedUtc=trim(self.start - timedelta(seconds=60)),
            finishedUtc=trim(self.finish + timedelta(seconds=60)),
        )

    def tamper_asset(self) -> None:
        self.examples_data["entries"][0]["summary"] = "tampered fixture summary"
        self._write_hap()

    def tamper_manifest(self) -> None:
        self.module["app"]["bundleName"] = "com.example.tampered"
        self._write_hap()

    def tamper_permissions(self) -> None:
        self.module["module"]["requestPermissions"].append(
            {"name": "ohos.permission.INTERNET"}
        )
        self._write_hap()

    def tamper_kernel(self) -> None:
        self.kernel = b"kernel-blob-tampered-9999"
        self._write_hap()

    def add_extra_entry(self) -> None:
        with zipfile.ZipFile(self.hap, "a", zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr("extra/notes.txt", b"synthetic tamper")


def _inject_duplicate_key(path: Path, key: str) -> None:
    text = path.read_text(encoding="utf-8")
    needle = f'"{key}":'
    replacement = f'"{key}":true,"{key}":'
    updated = text.replace(needle, replacement, 1)
    assert updated != text, f"duplicate-key injection missed {key} in {path.name}"
    path.write_text(updated, encoding="utf-8")


# --------------------------------------------------------------------------
# Fixture self-check: runs even before the verifier module exists.
# --------------------------------------------------------------------------


class FixtureSelfCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.fx = Fixture(Path(self._tmp.name))

    def test_derived_metrics_match_contract(self) -> None:
        self.assertEqual(self.fx.metrics["examples"], 340)
        self.assertEqual(self.fx.metrics["runnerPasses"], 340)
        self.assertEqual(self.fx.metrics["tutorials"], 340)
        self.assertEqual(self.fx.metrics["lessons"], 340)
        self.assertEqual(self.fx.metrics["exerciseAnswers"], 440)
        self.assertEqual(self.fx.metrics["fixtures"], 340)
        self.assertEqual(self.fx.metrics["semanticOperations"], 10)
        self.assertEqual(self.fx.metrics["tools"], 16)

    def test_report_log_and_capture_agree(self) -> None:
        self.assertEqual(self.fx.report["status"], "passed")
        self.assertIs(self.fx.report["passed"], True)
        self.assertEqual(self.fx.report["platform"], "ohos")
        self.assertEqual(self.fx.report["failures"], [])
        self.assertEqual(self.fx.capture["processLogSha256"], sha256_file(self.fx.log_path))
        self.assertEqual(self.fx.capture["reportSha256"], sha256_file(self.fx.report_path))
        self.assertEqual(self.fx.capture["installedHapSha256"], sha256_file(self.fx.hap))
        lines = _find_result_lines(self.fx.log_path.read_text(encoding="utf-8"))
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(_result_payload(lines[0])), self.fx.report)

    def test_run_id_encodes_pid_and_start_micros(self) -> None:
        head, micros_text, seq = self.fx.report["runId"].split("-")
        self.assertEqual(int(head), self.fx.capture["processId"])
        self.assertEqual(int(micros_text), micros(self.fx.start))
        self.assertEqual(seq, "0")

    def test_capture_time_envelops_report(self) -> None:
        started = datetime.strptime(self.fx.report["startedUtc"], "%Y-%m-%dT%H:%M:%S.%fZ")
        finished = datetime.strptime(self.fx.report["finishedUtc"], "%Y-%m-%dT%H:%M:%S.%fZ")
        capture_start = datetime.strptime(self.fx.capture["startedUtc"], "%Y-%m-%dT%H:%M:%S.%fZ")
        capture_finish = datetime.strptime(self.fx.capture["finishedUtc"], "%Y-%m-%dT%H:%M:%S.%fZ")
        self.assertLessEqual(capture_start, started)
        self.assertGreaterEqual(capture_finish, finished)
        self.assertEqual(self.fx.capture["processId"], self.fx.pid)
        self.assertIsInstance(self.fx.capture["processId"], int)

    def test_hap_contains_required_entries(self) -> None:
        with zipfile.ZipFile(self.fx.hap) as bundle:
            names = bundle.namelist()
            module = json.loads(bundle.read("module.json"))
            kernel = bundle.read(KERNEL_ENTRY)
        self.assertIn("module.json", names)
        self.assertIn(LIB_ENTRY, names)
        self.assertIn(KERNEL_ENTRY, names)
        for entry_path in CONTENT_ENTRY.values():
            self.assertIn(entry_path, names)
        self.assertEqual(module["app"]["bundleName"], BUNDLE)
        self.assertTrue(kernel)

    def test_artifact_hashes_match_hap(self) -> None:
        with zipfile.ZipFile(self.fx.hap) as bundle:
            kernel = sha256_bytes(bundle.read(KERNEL_ENTRY))
            examples = sha256_bytes(bundle.read(CONTENT_ENTRY["examples.json"]))
        self.assertEqual(self.fx.artifact["hapSha256"], sha256_file(self.fx.hap))
        self.assertEqual(self.fx.artifact["kernelSha256"], kernel)
        self.assertEqual(self.fx.artifact["contentAssets"]["examples.json"]["sha256"], examples)
        self.assertEqual(self.fx.artifact["mode"], "harness")
        self.assertEqual(self.fx.artifact["status"], "PASS")
        self.assertEqual(self.fx.artifact["sourceDependencies"]["status"], "PASS")
        for group in ("app", "core", "re_editor"):
            self.assertTrue(self.fx.artifact["sourceDependencies"]["sources"][group])


# --------------------------------------------------------------------------
# Verifier behaviour. Skipped until the implementation file exists.
# --------------------------------------------------------------------------


@unittest.skipIf(MODULE is None, "verify_json_device_evidence.py is not present yet")
class EvidenceVerifierTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.fx = Fixture(Path(self._tmp.name))

    # -- helpers ---------------------------------------------------------

    def _verify(self, hap=None):
        return MODULE.verify_evidence(
            Path(hap if hap is not None else self.fx.hap),
            self.fx.artifact_path,
            self.fx.log_path,
            self.fx.report_path,
            self.fx.capture_path,
        )

    def _assert_accepted(self) -> dict:
        try:
            result = self._verify()
        except ValueError as exc:
            self.fail(f"expected acceptance but the verifier rejected the evidence: {exc}")
        self.assertIsInstance(result, dict)
        self.assertIs(result.get("passed"), True, msg=f"expected acceptance, got {result}")
        return result

    def _assert_rejected(self) -> None:
        try:
            result = self._verify()
        except ValueError:
            return
        self.assertIsInstance(result, dict)
        self.assertFalse(
            result.get("passed") is True,
            msg=f"expected rejection, got {result}",
        )

    def _rebuild_consistent(self, **overrides) -> None:
        data = dict(self.fx.report)
        for key, value in overrides.items():
            if value is _DROP:
                data.pop(key, None)
            else:
                data[key] = value
        self.fx._write_report(data)
        self.fx._write_log()
        self.fx._write_capture()

    # -- baseline --------------------------------------------------------

    def test_accepts_consistent_synthetic_evidence(self) -> None:
        result = self._assert_accepted()
        metrics = result.get("metrics")
        self.assertIsInstance(metrics, dict, msg=f"missing metrics block: {result}")
        for key in (
            "examples",
            "runnerPasses",
            "tutorials",
            "lessons",
            "exerciseAnswers",
            "fixtures",
            "semanticOperations",
        ):
            self.assertEqual(metrics.get(key), self.fx.metrics[key], msg=key)

    def test_rejects_log_only_cleanup_error(self) -> None:
        # Protocol decision: the log and the exported report must match fully.
        # A log-only cleanupError is a mismatch and must be rejected.
        self.fx.set_log_field(cleanupError="staged cleanup failed")
        self._assert_rejected()

    def test_accepts_millisecond_precision_started_utc(self) -> None:
        self.fx.use_millisecond_timestamps()
        self._assert_accepted()

    def test_accepts_prefixed_marker_line(self) -> None:
        line = (
            "10-22 12:00:05.000  5271  5271 I A0c0d0/JSON: QFLI_JSON_VERIFY_RESULT "
            + _compact(self.fx.report)
        )
        self.fx._write_log(PROGRESS_LINE + "\n" + line + "\n")
        self.fx._write_capture()
        self._assert_accepted()

    def test_accepts_per_branch_semantic_accumulation(self) -> None:
        fixture = Fixture(Path(self._tmp.name) / "both", n_patch=7, n_merge=3, n_both=1)
        self.fx = fixture
        self.assertEqual(fixture.metrics["semanticOperations"], 12)
        self._assert_accepted()

    def test_cli_exit_codes_and_output(self) -> None:
        output = Path(self._tmp.name) / "cli-out.json"
        command = [
            sys.executable,
            str(MODULE_PATH),
            "--hap", str(self.fx.hap),
            "--artifact", str(self.fx.artifact_path),
            "--process-log", str(self.fx.log_path),
            "--report", str(self.fx.report_path),
            "--capture", str(self.fx.capture_path),
            "--output", str(output),
        ]
        ok = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, msg=ok.stdout + ok.stderr)
        self.assertTrue(json.loads(output.read_text(encoding="utf-8")).get("passed"))

        self.fx.set_report(runnerPasses=1)
        bad_output = Path(self._tmp.name) / "cli-bad.json"
        command[-1] = str(bad_output)
        bad = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1, msg=bad.stdout + bad.stderr)
        exported = json.loads(bad_output.read_text(encoding="utf-8"))
        self.assertIs(exported.get("passed"), False)

    # -- identity and time ----------------------------------------------

    def test_rejects_stale_run_id(self) -> None:
        self.fx.set_report(runId=f"{self.fx.pid}-{micros(self.fx.start) - 86_400_000_000}-0")
        self._assert_rejected()

    def test_rejects_run_id_time_not_matching_started_utc(self) -> None:
        self.fx.set_report(runId=f"{self.fx.pid}-{micros(self.fx.start) + 1}-0")
        self._assert_rejected()

    def test_rejects_run_id_pid_not_matching_capture(self) -> None:
        self.fx.set_report(runId=f"{self.fx.pid + 1}-{micros(self.fx.start)}-0")
        self._assert_rejected()

    def test_rejects_capture_pid_mismatch(self) -> None:
        self.fx._write_capture(processId=self.fx.pid + 1)
        self._assert_rejected()

    def test_rejects_capture_time_not_enveloping_report(self) -> None:
        self.fx._write_capture(startedUtc=stamp(self.fx.start + timedelta(seconds=30)))
        self._assert_rejected()

    def test_rejects_capture_window_before_report_finish(self) -> None:
        self.fx._write_capture(finishedUtc=stamp(self.fx.start - timedelta(seconds=1)))
        self._assert_rejected()

    def test_rejects_capture_schema_version(self) -> None:
        self.fx._write_capture(schemaVersion=2)
        self._assert_rejected()

    def test_rejects_capture_empty_device_id(self) -> None:
        self.fx._write_capture(deviceId="")
        self._assert_rejected()

    def test_rejects_capture_empty_grant(self) -> None:
        self.fx._write_capture(grant="")
        self._assert_rejected()

    def test_rejects_capture_bundle_mismatch(self) -> None:
        self.fx._write_capture(bundleName="com.example.other")
        self._assert_rejected()

    def test_rejects_capture_missing_field(self) -> None:
        payload = dict(self.fx.capture)
        payload.pop("grant")
        self.fx.capture_path.write_text(_dumps(payload) + "\n", encoding="utf-8")
        self._assert_rejected()

    def test_rejects_capture_hap_sha_mismatch(self) -> None:
        self.fx._write_capture(installedHapSha256="0" * 64)
        self._assert_rejected()

    def test_rejects_capture_log_sha_mismatch(self) -> None:
        self.fx._write_capture(processLogSha256="0" * 64)
        self._assert_rejected()

    def test_rejects_capture_report_sha_mismatch(self) -> None:
        self.fx._write_capture(reportSha256="0" * 64)
        self._assert_rejected()

    def test_rejects_boolean_process_id(self) -> None:
        self.fx._write_capture(processId=True)
        self._assert_rejected()

    def test_rejects_duplicate_capture_key(self) -> None:
        _inject_duplicate_key(self.fx.capture_path, "grant")
        self._assert_rejected()

    # -- report status ---------------------------------------------------

    def test_rejects_running_placeholder(self) -> None:
        self._rebuild_consistent(status="running", passed=False)
        self._assert_rejected()

    def test_rejects_running_placeholder_without_finished_utc(self) -> None:
        self._rebuild_consistent(status="running", passed=False, finishedUtc=_DROP)
        self._assert_rejected()

    def test_rejects_failed_report(self) -> None:
        self._rebuild_consistent(status="failed", passed=False)
        self._assert_rejected()

    def test_rejects_integer_passed(self) -> None:
        self.fx.set_report(passed=1)
        self._assert_rejected()

    def test_rejects_non_ohos_platform(self) -> None:
        self.fx.set_report(platform="windows")
        self._assert_rejected()

    def test_rejects_non_empty_failure_list(self) -> None:
        self.fx.set_report(failures=["json-example-001: runner exit=1"])
        self._assert_rejected()

    def test_rejects_missing_failure_list(self) -> None:
        self._rebuild_consistent(failures=_DROP)
        self._assert_rejected()

    def test_rejects_duplicate_report_key(self) -> None:
        _inject_duplicate_key(self.fx.report_path, "passed")
        self.fx._write_log()
        self.fx._write_capture()
        self._assert_rejected()

    # -- counts and types ------------------------------------------------

    def test_rejects_count_shortfall(self) -> None:
        self.fx.set_report(runnerPasses=self.fx.metrics["runnerPasses"] - 1)
        self._assert_rejected()

    def test_rejects_matched_but_under_minimum_examples(self) -> None:
        fixture = Fixture(Path(self._tmp.name) / "small-examples", n_examples=300)
        self.fx = fixture
        self.assertLess(fixture.metrics["examples"], MIN_ENTRIES)
        self._assert_rejected()

    def test_rejects_matched_but_under_minimum_tutorials(self) -> None:
        fixture = Fixture(Path(self._tmp.name) / "small-tutorials", n_tutorials=300)
        self.fx = fixture
        self.assertLess(fixture.metrics["tutorials"], MIN_ENTRIES)
        self._assert_rejected()

    def test_rejects_missing_count(self) -> None:
        self._rebuild_consistent(fixtures=_DROP)
        self._assert_rejected()

    def test_rejects_boolean_count(self) -> None:
        self.fx.set_report(examples=True)
        self._assert_rejected()

    def test_rejects_string_count(self) -> None:
        self.fx.set_report(lessons="340")
        self._assert_rejected()

    def test_rejects_tools_contract_change(self) -> None:
        self.fx.set_report(tools=TOOLS_CONTRACT - 1)
        self._assert_rejected()

    # -- log versus report ----------------------------------------------

    def test_rejects_log_report_mismatch(self) -> None:
        self.fx.set_log_field(runnerPasses=self.fx.metrics["runnerPasses"] - 1)
        self._assert_rejected()

    def test_rejects_duplicate_marker(self) -> None:
        self.fx.duplicate_marker()
        self._assert_rejected()

    def test_rejects_duplicate_json_key(self) -> None:
        raw = _compact(self.fx.report).replace('"passed":', '"passed":true,"passed":', 1)
        self.fx._write_log("QFLI_JSON_VERIFY_RESULT " + raw + "\n")
        self.fx._write_capture()
        self._assert_rejected()

    def test_rejects_missing_marker(self) -> None:
        self.fx._write_log(PROGRESS_LINE + "\n")
        self.fx._write_capture()
        self._assert_rejected()

    def test_rejects_unparsable_marker_payload(self) -> None:
        self.fx._write_log("QFLI_JSON_VERIFY_RESULT {not json}\n")
        self.fx._write_capture()
        self._assert_rejected()

    # -- artifact --------------------------------------------------------

    def test_rejects_artifact_failed_status(self) -> None:
        self.fx._write_artifact(status="FAIL", passed=False)
        self._assert_rejected()

    def test_rejects_artifact_normal_mode(self) -> None:
        self.fx._write_artifact(mode="normal")
        self._assert_rejected()

    def test_rejects_artifact_source_dependencies_not_pass(self) -> None:
        dependencies = dict(self.fx.artifact["sourceDependencies"])
        dependencies["status"] = "BLOCKED"
        self.fx._write_artifact(sourceDependencies=dependencies)
        self._assert_rejected()

    def test_rejects_artifact_missing_source_dependencies(self) -> None:
        self.fx.drop_artifact_key("sourceDependencies")
        self._assert_rejected()

    def test_rejects_artifact_empty_source_group(self) -> None:
        dependencies = {
            "status": "PASS",
            "sources": {
                "app": [{"path": "app/lib/main.dart", "sha256": "0" * 64}],
                "core": [],
                "re_editor": [{"path": "re_editor/lib/re_editor.dart", "sha256": "2" * 64}],
            },
        }
        self.fx._write_artifact(sourceDependencies=dependencies)
        self._assert_rejected()

    def test_rejects_artifact_extra_permission(self) -> None:
        self.fx._write_artifact(permissions=[PERMISSION, "ohos.permission.INTERNET"])
        self._assert_rejected()

    def test_rejects_artifact_bundle_mismatch(self) -> None:
        self.fx._write_artifact(bundleName="com.example.other")
        self._assert_rejected()

    def test_rejects_artifact_content_sha_mismatch(self) -> None:
        assets = json.loads(json.dumps(self.fx.artifact["contentAssets"]))
        assets["examples.json"]["sha256"] = "0" * 64
        self.fx._write_artifact(contentAssets=assets)
        self._assert_rejected()

    def test_rejects_artifact_missing_content_asset(self) -> None:
        assets = json.loads(json.dumps(self.fx.artifact["contentAssets"]))
        assets.pop("tutorials.json")
        self.fx._write_artifact(contentAssets=assets)
        self._assert_rejected()

    def test_rejects_artifact_kernel_sha_mismatch(self) -> None:
        self.fx._write_artifact(kernelSha256="0" * 64)
        self._assert_rejected()

    def test_rejects_artifact_hap_sha_mismatch(self) -> None:
        self.fx._write_artifact(hapSha256="0" * 64)
        self._assert_rejected()

    def test_rejects_duplicate_artifact_key(self) -> None:
        _inject_duplicate_key(self.fx.artifact_path, "passed")
        self._assert_rejected()

    # -- packaged input changes -----------------------------------------

    def test_rejects_changed_hap_bytes(self) -> None:
        self.fx.add_extra_entry()
        self._assert_rejected()

    def test_rejects_changed_asset(self) -> None:
        self.fx.tamper_asset()
        self._assert_rejected()

    def test_rejects_changed_manifest_bundle(self) -> None:
        self.fx.tamper_manifest()
        self._assert_rejected()

    def test_rejects_added_permission_in_manifest(self) -> None:
        self.fx.tamper_permissions()
        self._assert_rejected()

    def test_rejects_changed_kernel(self) -> None:
        self.fx.tamper_kernel()
        self._assert_rejected()

    # -- invalid input ---------------------------------------------------

    def test_invalid_input_raises_value_error(self) -> None:
        missing = Path(self._tmp.name) / "missing.hap"
        with self.assertRaises(ValueError):
            self._verify(hap=missing)

    def test_malformed_capture_raises_value_error(self) -> None:
        self.fx.capture_path.write_text("{not json}\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self._verify()


    def test_rejects_uppercase_report_status(self):
        self.fx.set_report(status="PASSED")
        self._assert_rejected()

    def test_rejects_padded_report_status(self):
        self.fx.set_report(status="  passed  ")
        self._assert_rejected()

    def test_accepts_marker_literal_inside_json_value(self):
        self.fx.set_report(note="QFLI_JSON_VERIFY_RESULT literal inside JSON")
        self._assert_accepted()

    def test_rejects_self_consistent_old_capture_before_hap_inspection(self):
        self.fx.start -= timedelta(days=1)
        self.fx.finish -= timedelta(days=1)
        self.fx._write_report(self.fx._base_report())
        self.fx._write_log()
        self.fx._write_capture()
        self._assert_rejected()

    def test_rejects_missing_artifact_inspection_time(self):
        self.fx.drop_artifact_key("inspectedUtc")
        self._assert_rejected()

    def test_rejects_compiled_bundle_even_with_forged_artifact_metadata(self):
        self.fx.tamper_manifest()
        self.fx._write_artifact(bundleName=BUNDLE)
        self.fx._write_capture()
        self._assert_rejected()

    def test_rejects_compiled_permission_even_with_forged_artifact_metadata(self):
        self.fx.tamper_permissions()
        self.fx._write_artifact(permissions=[PERMISSION])
        self.fx._write_capture()
        self._assert_rejected()

    def test_rejects_missing_engine_with_consistent_hashes(self):
        with zipfile.ZipFile(self.fx.hap) as bundle:
            entries = [(info.filename, bundle.read(info)) for info in bundle.infolist() if info.filename != LIB_ENTRY]
        with zipfile.ZipFile(self.fx.hap, "w", zipfile.ZIP_DEFLATED) as bundle:
            for name, value in entries:
                bundle.writestr(name, value)
        self.fx._write_artifact()
        self.fx._write_capture()
        self._assert_rejected()

    def _refresh_hap_hash_only(self):
        self.fx.artifact["hapSha256"] = sha256_file(self.fx.hap)
        self.fx.artifact_path.write_text(_dumps(self.fx.artifact), encoding="utf-8")
        self.fx._write_capture()

    def test_corrupt_member_raises_value_error(self):
        with zipfile.ZipFile(self.fx.hap) as bundle:
            info = bundle.getinfo(KERNEL_ENTRY)
        data = bytearray(self.fx.hap.read_bytes())
        name_len, extra_len = struct.unpack_from("<HH", data, info.header_offset + 26)
        payload_offset = info.header_offset + 30 + name_len + extra_len
        data[payload_offset] ^= 255
        self.fx.hap.write_bytes(data)
        self._refresh_hap_hash_only()
        with self.assertRaises(ValueError):
            self._verify()

    def test_encrypted_member_raises_value_error(self):
        with zipfile.ZipFile(self.fx.hap) as bundle:
            infos = bundle.infolist()
            central = bundle.start_dir
        data = bytearray(self.fx.hap.read_bytes())
        for info in infos:
            offset = info.header_offset + 6
            struct.pack_into("<H", data, offset, struct.unpack_from("<H", data, offset)[0] | 1)
        while data[central:central + 4] == b"PK\x01\x02":
            offset = central + 8
            struct.pack_into("<H", data, offset, struct.unpack_from("<H", data, offset)[0] | 1)
            name_len, extra_len, comment_len = struct.unpack_from("<HHH", data, central + 28)
            central += 46 + name_len + extra_len + comment_len
        self.fx.hap.write_bytes(data)
        self._refresh_hap_hash_only()
        with self.assertRaises(ValueError):
            self._verify()

    def test_rejects_content_alias_instead_of_entries(self):
        data = dict(self.fx.examples_data)
        data["examples"] = data.pop("entries")
        with self.assertRaises(ValueError):
            MODULE.derive_catalog_metrics(data, self.fx.tutorials_data)

    def test_rejects_string_input_fixtures(self):
        self.fx.examples_data["entries"][0]["inputFixtures"] = "{}"
        with self.assertRaises(ValueError):
            MODULE.derive_catalog_metrics(self.fx.examples_data, self.fx.tutorials_data)


class _Drop:
    """Sentinel used to remove a report key inside ``_rebuild_consistent``."""


_DROP = _Drop()


if __name__ == "__main__":
    unittest.main(verbosity=2)