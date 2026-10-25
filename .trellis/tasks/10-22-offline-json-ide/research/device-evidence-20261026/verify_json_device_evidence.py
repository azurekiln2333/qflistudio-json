"""Offline integrity verifier for QFLIJson device evidence.

This module never invokes a build tool, a device tool, or the network. It only
reads files that a caller already captured and checks that they agree with each
other:

* the HAP archive and the HAP-inspector ``artifact``;
* the exported verification ``report`` written by
  ``runJsonVerificationReport`` in ``lib/json/json_verification_report.dart``;
* the device ``process_log`` that carries one ``QFLI_JSON_VERIFY_RESULT``
  marker line;
* the ``capture`` metadata that records the device run.

The verifier validates completeness and internal consistency. It does **not**
prove that a package was actually installed, that the hardware is real, or that
a captured grant is authoritative. A synthetic fixture that the checks accept
is still only a synthetic fixture and must never be described as a device pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

__all__ = [
    "EvidenceValidationError",
    "derive_catalog_metrics",
    "verify_evidence",
]

MARKER = "QFLI_JSON_VERIFY_RESULT"
BUNDLE_NAME = "com.azurekiln.qfli.json"
CLIPBOARD_PERMISSION = "ohos.permission.READ_PASTEBOARD"
CONTENT_NAMES = ("catalog_audit.json", "examples.json", "tutorials.json")
KERNEL_ENTRY = "resources/rawfile/flutter_assets/kernel_blob.bin"
CONTENT_ENTRY_PREFIX = "resources/rawfile/flutter_assets/assets/content/"
TOOLS_CONTRACT = 16
MIN_EXAMPLES = 320
MIN_TUTORIALS = 320

METRIC_KEYS = (
    "examples",
    "runnerPasses",
    "tutorials",
    "lessons",
    "exerciseAnswers",
    "fixtures",
    "semanticOperations",
)

# Input limits. They bound every file read and every ZIP member so a malicious
# or accidental input fails closed instead of exhausting memory.
MAX_HAP_BYTES = 512 * 1024**2
MAX_JSON_BYTES = 16 * 1024**2
MAX_LOG_BYTES = 16 * 1024**2
MAX_ZIP_ENTRIES = 200_000
MAX_ZIP_ENTRY_UNCOMPRESSED = 256 * 1024**2
MAX_ZIP_TOTAL_UNCOMPRESSED = 768 * 1024**2
MAX_ZIP_COMPRESSION_RATIO = 2000

CHUNK = 1024 * 1024
RUN_ID_RE = re.compile(r"^(\d+)-(\d+)-(\d+)$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

DISCLAIMER = (
    "This verifier checks only the consistency of the supplied evidence. "
    "It does not independently prove installation, hardware origin, or the "
    "authenticity of the captured grant. An accepted synthetic fixture is "
    "not a device pass."
)


class EvidenceValidationError(ValueError):
    """The supplied evidence is missing, invalid, or mutually inconsistent."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceValidationError(message)


def _read_bytes(path, limit: int, label: str) -> bytes:
    p = Path(path)
    if not p.exists():
        raise EvidenceValidationError(f"{label} does not exist: {p}")
    if not p.is_file():
        raise EvidenceValidationError(f"{label} is not a regular file: {p}")
    try:
        size = p.stat().st_size
    except OSError as exc:  # pragma: no cover - platform dependent
        raise EvidenceValidationError(f"{label} cannot be stat'ed: {exc}") from exc
    _require(size <= limit, f"{label} exceeds the {limit}-byte input limit")
    try:
        data = p.read_bytes()
    except OSError as exc:
        raise EvidenceValidationError(f"{label} cannot be read: {exc}") from exc
    _require(len(data) <= limit, f"{label} grew past the {limit}-byte input limit")
    return data


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path, limit: int, label: str) -> str:
    p = Path(path)
    if not p.exists():
        raise EvidenceValidationError(f"{label} does not exist: {p}")
    if not p.is_file():
        raise EvidenceValidationError(f"{label} is not a regular file: {p}")
    try:
        if p.stat().st_size > limit:
            raise EvidenceValidationError(f"{label} exceeds the {limit}-byte input limit")
    except OSError as exc:  # pragma: no cover - platform dependent
        raise EvidenceValidationError(f"{label} cannot be stat'ed: {exc}") from exc
    digest = hashlib.sha256()
    seen = 0
    try:
        with p.open("rb") as source:
            for chunk in iter(lambda: source.read(CHUNK), b""):
                seen += len(chunk)
                if seen > limit:
                    raise EvidenceValidationError(
                        f"{label} grew past the {limit}-byte input limit"
                    )
                digest.update(chunk)
    except OSError as exc:
        raise EvidenceValidationError(f"{label} cannot be read: {exc}") from exc
    return digest.hexdigest()


def _no_duplicate_pairs(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise EvidenceValidationError(f"duplicate JSON key: {key!r}")
        seen[key] = value
    return seen


def _loads_no_dupes(text: str, label: str):
    try:
        return json.loads(text, object_pairs_hook=_no_duplicate_pairs)
    except EvidenceValidationError:
        raise
    except (json.JSONDecodeError, RecursionError) as exc:
        raise EvidenceValidationError(f"{label} is not valid JSON: {exc}") from exc


def _decode_json_bytes(data: bytes, label: str) -> dict:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise EvidenceValidationError(f"{label} is not UTF-8: {exc}") from exc
    value = _loads_no_dupes(text, label)
    _require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _load_json_file(path, label: str, limit: int = MAX_JSON_BYTES) -> tuple[dict, bytes]:
    data = _read_bytes(path, limit, label)
    return _decode_json_bytes(data, label), data


def _hex64(value, label: str) -> str:
    _require(
        isinstance(value, str) and SHA256_RE.fullmatch(value) is not None,
        f"{label} must be a lowercase 64-character SHA-256 hex string",
    )
    return value


def _as_int(value, label: str, *, minimum: int | None = None, maximum: int | None = None) -> int:
    # ``type(...) is int`` rejects ``bool``, which is an ``int`` subclass.
    _require(type(value) is int, f"{label} must be an integer (bool is rejected)")
    if minimum is not None:
        _require(value >= minimum, f"{label} must be at least {minimum}")
    if maximum is not None:
        _require(value <= maximum, f"{label} must be at most {maximum}")
    return value


def _parse_utc(value, label: str) -> datetime:
    _require(isinstance(value, str) and value.strip(), f"{label} must be a non-empty ISO-8601 string")
    text = value.strip()
    normalized = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EvidenceValidationError(f"{label} is not valid ISO-8601: {exc}") from exc
    _require(parsed.tzinfo is not None, f"{label} must carry an explicit UTC offset")
    if parsed.utcoffset() != timedelta(0):
        raise EvidenceValidationError(f"{label} must be in UTC")
    return parsed.astimezone(timezone.utc)


def _epoch_micros(moment: datetime) -> int:
    delta = moment - EPOCH
    return (delta.days * 86_400 + delta.seconds) * 1_000_000 + delta.microseconds


def _is_nonempty(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    return False


def _deep_equal(left, right, depth: int = 0) -> bool:
    if depth > 200:
        raise EvidenceValidationError("evidence JSON is nested too deeply to compare")
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return False
        return all(_deep_equal(left[key], right[key], depth + 1) for key in left)
    if isinstance(left, list):
        if len(left) != len(right):
            return False
        return all(_deep_equal(a, b, depth + 1) for a, b in zip(left, right))
    return left == right


def _normalize_permissions(value, label: str) -> list[str]:
    _require(isinstance(value, list), f"{label} must be a list")
    names = []
    for item in value:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict) and isinstance(item.get("name"), str):
            names.append(item["name"])
        else:
            raise EvidenceValidationError(f"{label} contains an unsupported permission entry")
    return names


def _artifact_content_shas(artifact: dict) -> dict[str, str]:
    assets = artifact.get("contentAssets")
    _require(isinstance(assets, dict), "artifact.contentAssets must be an object")
    result = {}
    for name in CONTENT_NAMES:
        entry = assets.get(name)
        _require(isinstance(entry, dict), f"artifact.contentAssets is missing {name}")
        result[name] = _hex64(
            entry.get("sha256"),
            f"artifact.contentAssets[{name}].sha256",
        )
    return result


def _entries(document: dict, key: str, label: str) -> list[dict]:
    _require(isinstance(document, dict), f"{label} must be a JSON object")
    entries = document.get("entries")
    _require(isinstance(entries, list), f"{label} must contain an entries array")
    for index, entry in enumerate(entries):
        _require(
            isinstance(entry, dict),
            f"{label}.entries[{index}] must be a JSON object",
        )
    return entries


def _lessons(tutorial: dict) -> list[dict]:
    lessons = tutorial.get("lessons", [])
    _require(isinstance(lessons, list), "tutorial lessons must be an array")
    _require(all(isinstance(lesson, dict) for lesson in lessons), "every lesson must be an object")
    return lessons


def _exercises(lesson: dict) -> list:
    exercises = lesson.get("exercises", [])
    _require(isinstance(exercises, list), "lesson exercises must be an array")
    return exercises


def _fixture_count(example: dict) -> int:
    fixtures = example.get("inputFixtures", {})
    _require(isinstance(fixtures, dict), "inputFixtures must be an object")
    return len(fixtures)


def _semantic_operation_count(example: dict) -> int:
    code = example.get("code")
    _require(isinstance(code, str), "example code must be a JSON string")
    value = _loads_no_dupes(code, "example code")
    if not isinstance(value, dict):
        return 0
    # Count each matching branch once. One example can carry both the patch
    # and the merge promise, so it contributes two operations, mirroring
    # verifyJsonCatalog in lib/json/json_catalog_verification.dart.
    count = 0
    if "operations" in value and "expected" in value:
        count += 1
    if "target" in value and "patch" in value and "expected" in value:
        count += 1
    return count


def derive_catalog_metrics(examples_document: dict, tutorials_document: dict) -> dict:
    """Derive the audit counters from a decoded examples/tutorials document.

    The result mirrors ``verifyJsonCatalog`` in
    ``lib/json/json_catalog_verification.dart``: one lesson per tutorial
    lesson, one answer per exercise, one fixture per declared input fixture,
    and one semantic operation per matching branch (an example may carry both
    the patch and merge promises, so it can add two). ``runnerPasses`` equals
    the example count because a passing catalog runs every example exactly
    once; it is a necessary consequence of a pass, not a static measurement.
    """
    examples = _entries(examples_document, "examples", "examples document")
    tutorials = _entries(tutorials_document, "tutorials", "tutorials document")

    lessons = 0
    exercise_answers = 0
    for tutorial in tutorials:
        for lesson in _lessons(tutorial):
            lessons += 1
            exercise_answers += len(_exercises(lesson))

    fixtures = sum(_fixture_count(example) for example in examples)
    semantic = sum(_semantic_operation_count(example) for example in examples)

    return {
        "examples": len(examples),
        "runnerPasses": len(examples),
        "tutorials": len(tutorials),
        "lessons": lessons,
        "exerciseAnswers": exercise_answers,
        "fixtures": fixtures,
        "semanticOperations": semantic,
        "tools": TOOLS_CONTRACT,
    }


def _guard_zip_members(infos: list[zipfile.ZipInfo]) -> None:
    _require(len(infos) <= MAX_ZIP_ENTRIES, "HAP has too many archive entries")
    total = 0
    for info in infos:
        _require(
            info.file_size <= MAX_ZIP_ENTRY_UNCOMPRESSED,
            f"HAP member is too large: {info.filename}",
        )
        total += info.file_size
        _require(
            total <= MAX_ZIP_TOTAL_UNCOMPRESSED,
            "HAP uncompressed size exceeds the total limit",
        )
        if info.compress_size:
            _require(
                info.file_size <= info.compress_size * MAX_ZIP_COMPRESSION_RATIO,
                f"HAP member has a suspicious compression ratio: {info.filename}",
            )


def _hash_zip_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    digest = hashlib.sha256()
    seen = 0
    with archive.open(info) as source:
        for chunk in iter(lambda: source.read(CHUNK), b""):
            seen += len(chunk)
            _require(
                seen <= MAX_ZIP_ENTRY_UNCOMPRESSED,
                f"HAP member decompressed past the per-entry limit: {info.filename}",
            )
            digest.update(chunk)
    return digest.hexdigest()


def _read_zip_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> bytes:
    _require(
        info.file_size <= MAX_JSON_BYTES,
        f"HAP member is too large: {info.filename}",
    )
    data = bytearray()
    with archive.open(info) as source:
        for chunk in iter(lambda: source.read(CHUNK), b""):
            data.extend(chunk)
            _require(
                len(data) <= MAX_JSON_BYTES,
                f"HAP member decompressed past the per-entry limit: {info.filename}",
            )
    return bytes(data)


def _scan_hap(hap_path) -> dict:
    hap_sha = _sha256_file(hap_path, MAX_HAP_BYTES, "HAP")
    try:
        archive = zipfile.ZipFile(hap_path)
    except (zipfile.BadZipFile, OSError) as exc:
        raise EvidenceValidationError(f"HAP is not a readable ZIP archive: {exc}") from exc

    with archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        _guard_zip_members(infos)
        names = [info.filename for info in infos]
        _require(len(names) == len(set(names)), "HAP contains duplicate archive entry names")

        kernels = [
            info
            for info in infos
            if PurePosixPath(info.filename).name == "kernel_blob.bin"
        ]
        _require(len(kernels) == 1, "HAP must contain exactly one kernel_blob.bin")
        kernel = kernels[0]
        _require(
            kernel.filename == KERNEL_ENTRY,
            f"kernel_blob.bin must sit at {KERNEL_ENTRY}",
        )
        kernel_sha = _hash_zip_member(archive, kernel)

        by_name = {info.filename: info for info in infos}
        _require("module.json" in by_name, "HAP is missing compiled module.json")
        module = _decode_json_bytes(_read_zip_member(archive, by_name["module.json"]), "HAP module.json")
        _require(isinstance(module.get("app"), dict) and module["app"].get("bundleName") == BUNDLE_NAME,
                 "compiled HAP bundle identity is invalid")
        module_part = module.get("module")
        _require(isinstance(module_part, dict), "compiled HAP module section is missing")
        permissions = _normalize_permissions(module_part.get("requestPermissions"), "compiled HAP permissions")
        _require(permissions == [CLIPBOARD_PERMISSION], "compiled HAP must request only clipboard permission")
        engine = by_name.get("libs/x86_64/libflutter.so")
        _require(engine is not None and engine.file_size > 0, "HAP is missing x86_64 Flutter engine")
        content_sha = {}
        documents = {}
        for name in CONTENT_NAMES:
            entry_name = CONTENT_ENTRY_PREFIX + name
            info = by_name.get(entry_name)
            _require(info is not None, f"HAP is missing content entry: {entry_name}")
            data = _read_zip_member(archive, info)
            content_sha[name] = _sha256_bytes(data)
            if name in ("examples.json", "tutorials.json"):
                documents[name] = _decode_json_bytes(data, f"HAP {name}")

    _require(_sha256_file(hap_path, MAX_HAP_BYTES, "HAP") == hap_sha, "HAP changed during verification")
    return {
        "hapSha256": hap_sha,
        "kernelSha256": kernel_sha,
        "contentSha256": content_sha,
        "examplesDocument": documents["examples.json"],
        "tutorialsDocument": documents["tutorials.json"],
    }


def _extract_log_marker(log_bytes: bytes) -> dict:
    try:
        text = log_bytes.decode("utf-8", errors="replace")
    except Exception as exc:  # pragma: no cover - decode with replace cannot raise
        raise EvidenceValidationError(f"process log cannot be decoded: {exc}") from exc

    payload_lines = [line.split(MARKER + " ", 1)[1] for line in text.splitlines() if MARKER + " " in line]
    _require(len(payload_lines) == 1, "process log must contain exactly one result marker line")
    line = payload_lines[0]
    payload = line.strip()
    _require(payload, "process log marker is not followed by JSON")
    _require(
        len(payload) <= MAX_JSON_BYTES,
        "process log marker JSON exceeds the input limit",
    )
    value = _loads_no_dupes(payload, "process log marker")
    _require(isinstance(value, dict), "process log marker JSON must be an object")
    return value


def _validate_artifact(artifact: dict) -> dict:
    _require(artifact.get("passed") is True, "artifact.passed must be true")
    _require(artifact.get("status") == "PASS", "artifact.status must be PASS")
    _require(artifact.get("mode") == "harness", "artifact.mode must be harness")
    _require(
        artifact.get("bundleName") == BUNDLE_NAME,
        f"artifact.bundleName must be {BUNDLE_NAME}",
    )

    permissions = _normalize_permissions(artifact.get("permissions"), "artifact.permissions")
    _require(
        permissions == [CLIPBOARD_PERMISSION],
        f"artifact.permissions must contain only {CLIPBOARD_PERMISSION}",
    )

    source_dependencies = artifact.get("sourceDependencies")
    _require(isinstance(source_dependencies, dict), "artifact.sourceDependencies must be an object")
    _require(
        source_dependencies.get("status") == "PASS",
        "artifact.sourceDependencies.status must be PASS",
    )
    sources = source_dependencies.get("sources")
    _require(isinstance(sources, dict), "artifact.sourceDependencies.sources must be an object")
    for group in ("app", "core", "re_editor"):
        _require(
            isinstance(sources.get(group), list) and len(sources[group]) > 0,
            f"artifact.sourceDependencies.sources.{group} must be a non-empty list",
        )

    return {
        "inspectedUtc": _parse_utc(artifact.get("inspectedUtc"), "artifact.inspectedUtc"),
        "hapSha256": _hex64(artifact.get("hapSha256"), "artifact.hapSha256"),
        "kernelSha256": _hex64(artifact.get("kernelSha256"), "artifact.kernelSha256"),
        "contentSha256": _artifact_content_shas(artifact),
    }


def _validate_capture(capture: dict) -> dict:
    version = capture.get("schemaVersion")
    _require(type(version) is int and version == 1, "capture.schemaVersion must be the integer 1")
    _require(
        isinstance(capture.get("deviceId"), str) and capture["deviceId"].strip(),
        "capture.deviceId must be a non-empty string",
    )
    _require(capture.get("platform") == "ohos", "capture.platform must be ohos")
    _require(
        capture.get("bundleName") == BUNDLE_NAME,
        f"capture.bundleName must be {BUNDLE_NAME}",
    )
    _require(_is_nonempty(capture.get("grant")), "capture.grant must be non-empty")
    process_id = _as_int(capture.get("processId"), "capture.processId", minimum=1)

    started = _parse_utc(capture.get("startedUtc"), "capture.startedUtc")
    finished = _parse_utc(capture.get("finishedUtc"), "capture.finishedUtc")
    _require(started <= finished, "capture.startedUtc must not be after capture.finishedUtc")

    return {
        "processId": process_id,
        "startedUtc": started,
        "finishedUtc": finished,
        "installedHapSha256": _hex64(
            capture.get("installedHapSha256"), "capture.installedHapSha256"
        ),
        "processLogSha256": _hex64(
            capture.get("processLogSha256"), "capture.processLogSha256"
        ),
        "reportSha256": _hex64(capture.get("reportSha256"), "capture.reportSha256"),
    }


def _validate_report(report: dict) -> dict:
    _require(report.get("passed") is True, "report.passed must be true")
    status = report.get("status")
    _require(
        status == "passed",
        "report.status must be passed",
    )
    _require(report.get("platform") == "ohos", "report.platform must be ohos")

    run_id = report.get("runId")
    _require(isinstance(run_id, str), "report.runId must be a string")
    match = RUN_ID_RE.fullmatch(run_id)
    _require(match is not None, "report.runId must match <pid>-<utc-micros>-<sequence>")
    run_pid = _as_int(int(match.group(1)), "report.runId pid", minimum=1)
    run_micros = _as_int(int(match.group(2)), "report.runId microseconds", minimum=0)
    _as_int(int(match.group(3)), "report.runId sequence", minimum=0)

    started = _parse_utc(report.get("startedUtc"), "report.startedUtc")
    finished = _parse_utc(report.get("finishedUtc"), "report.finishedUtc")
    _require(started <= finished, "report.startedUtc must not be after report.finishedUtc")

    _require(
        report.get("failures") == [],
        "report.failures must be an empty list",
    )

    metrics = {}
    for key in METRIC_KEYS:
        metrics[key] = _as_int(report.get(key), f"report.{key}", minimum=0)
    tools = _as_int(report.get("tools"), "report.tools", minimum=0)
    _require(tools == TOOLS_CONTRACT, f"report.tools must be {TOOLS_CONTRACT}")

    _require(metrics["runnerPasses"] == metrics["examples"], "report.runnerPasses must equal report.examples")
    _require(metrics["examples"] >= MIN_EXAMPLES, f"report.examples must be at least {MIN_EXAMPLES}")
    _require(metrics["tutorials"] >= MIN_TUTORIALS, f"report.tutorials must be at least {MIN_TUTORIALS}")

    return {
        "runId": run_id,
        "runPid": run_pid,
        "runMicros": run_micros,
        "startedUtc": started,
        "finishedUtc": finished,
        "metrics": metrics,
        "tools": tools,
    }


def _verify_evidence(hap, artifact, process_log, report, capture) -> dict:
    """Verify that the supplied device evidence is complete and consistent.

    Returns a result dictionary on success. Raises ``EvidenceValidationError``
    (a ``ValueError`` subclass) for missing, malformed, or inconsistent input.
    """
    artifact_doc, _ = _load_json_file(artifact, "artifact")
    report_doc, report_bytes = _load_json_file(report, "report")
    capture_doc, _ = _load_json_file(capture, "capture")
    log_bytes = _read_bytes(process_log, MAX_LOG_BYTES, "process log")

    artifact_facts = _validate_artifact(artifact_doc)
    capture_facts = _validate_capture(capture_doc)
    report_facts = _validate_report(report_doc)
    log_marker = _extract_log_marker(log_bytes)
    _require(artifact_facts["inspectedUtc"] <= capture_facts["startedUtc"],
             "capture predates this HAP inspection (replayed evidence)")

    # Identity: bundle, platform, pid, run-id micros, and the UTC capture window.
    _require(
        capture_doc.get("bundleName") == artifact_doc.get("bundleName"),
        "capture.bundleName and artifact.bundleName must agree",
    )
    _require(
        report_facts["runPid"] == capture_facts["processId"],
        "report.runId pid and capture.processId must agree",
    )
    _require(
        report_facts["runMicros"] == _epoch_micros(report_facts["startedUtc"]),
        "report.runId microseconds must match report.startedUtc",
    )
    _require(
        capture_facts["startedUtc"] <= report_facts["startedUtc"],
        "capture.startedUtc must not be after report.startedUtc (stale evidence)",
    )
    _require(
        report_facts["finishedUtc"] <= capture_facts["finishedUtc"],
        "report.finishedUtc must not be after capture.finishedUtc (stale evidence)",
    )

    # Byte-level identity of the two captured input files (and the HAP).
    _require(
        _sha256_bytes(report_bytes) == capture_facts["reportSha256"],
        "report SHA-256 does not match capture.reportSha256",
    )
    _require(
        _sha256_bytes(log_bytes) == capture_facts["processLogSha256"],
        "process log SHA-256 does not match capture.processLogSha256",
    )

    hap_facts = _scan_hap(hap)
    _require(
        hap_facts["hapSha256"] == artifact_facts["hapSha256"],
        "HAP SHA-256 does not match artifact.hapSha256",
    )
    _require(
        hap_facts["hapSha256"] == capture_facts["installedHapSha256"],
        "HAP SHA-256 does not match capture.installedHapSha256",
    )
    _require(
        hap_facts["kernelSha256"] == artifact_facts["kernelSha256"],
        "kernel SHA-256 does not match artifact.kernelSha256",
    )
    for name in CONTENT_NAMES:
        _require(
            hap_facts["contentSha256"][name] == artifact_facts["contentSha256"][name],
            f"{name} SHA-256 does not match the artifact",
        )

    # Derive the audit counters from the packaged catalog, not from the report.
    derived = derive_catalog_metrics(
        hap_facts["examplesDocument"],
        hap_facts["tutorialsDocument"],
    )
    _require(
        derived["examples"] >= MIN_EXAMPLES,
        f"packaged examples count must be at least {MIN_EXAMPLES}",
    )
    _require(
        derived["tutorials"] >= MIN_TUTORIALS,
        f"packaged tutorials count must be at least {MIN_TUTORIALS}",
    )
    for key in METRIC_KEYS:
        _require(
            report_facts["metrics"][key] == derived[key],
            f"report.{key} ({report_facts['metrics'][key]}) must equal the packaged count ({derived[key]})",
        )
    _require(
        report_facts["tools"] == derived["tools"],
        f"report.tools must equal the fixed contract {TOOLS_CONTRACT}",
    )

    # The log marker and the exported report must match exactly, including all
    # nested contents. Any extra, missing, or different value rejects the run.
    _require(
        _deep_equal(log_marker, report_doc),
        "process log marker JSON and exported report differ in structure",
    )

    return {
        "passed": True,
        "scope": "evidence-consistency-only",
        "devicePassIndependentlyProven": False,
        "disclaimer": DISCLAIMER,
        "bundleName": BUNDLE_NAME,
        "platform": "ohos",
        "runId": report_facts["runId"],
        "processId": capture_facts["processId"],
        "hapSha256": hap_facts["hapSha256"],
        "kernelSha256": hap_facts["kernelSha256"],
        "contentSha256": dict(hap_facts["contentSha256"]),
        "metrics": derived,
        "checks": [
            "artifact identity and harness mode",
            "artifact clipboard-only permission",
            "artifact sourceDependencies PASS with three non-empty sources",
            "capture schema, device, bundle, grant, and integer process id",
            "report run id, status, platform, and metrics",
            "capture UTC window brackets the report window",
            "run-id pid and microsecond identity",
            "report and process-log SHA-256 match the capture",
            "HAP, kernel, and three content SHA-256 match the artifact",
            "packaged catalog counts match the report",
            "process-log marker equals the exported report",
        ],
    }


def verify_evidence(hap, artifact, process_log, report, capture) -> dict:
    """Validate supplied evidence, mapping malformed archive input to ValueError."""
    try:
        return _verify_evidence(hap, artifact, process_log, report, capture)
    except EvidenceValidationError:
        raise
    except (zipfile.BadZipFile, RuntimeError, zlib.error, EOFError, OSError, NotImplementedError) as error:
        raise EvidenceValidationError(f"unreadable evidence archive: {error}") from error


def _write_output(path, result: dict) -> None:
    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise EvidenceValidationError(f"cannot write output file: {exc}") from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the internal consistency of captured QFLIJson device evidence. "
            "This tool never runs a device command."
        )
    )
    parser.add_argument("--hap", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--process-log", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = verify_evidence(
            hap=args.hap,
            artifact=args.artifact,
            process_log=args.process_log,
            report=args.report,
            capture=args.capture,
        )
        _write_output(args.output, result)
        print(json.dumps({"passed": True, "runId": result.get("runId")}, separators=(",", ":")))
        return 0
    except (EvidenceValidationError, ValueError) as exc:
        failure = {
            "passed": False,
            "scope": "evidence-consistency-only",
            "devicePassIndependentlyProven": False,
            "disclaimer": DISCLAIMER,
            "error": str(exc),
            "kind": "invalid-evidence",
        }
    except Exception as exc:  # fail closed on any unexpected error
        failure = {
            "passed": False,
            "scope": "evidence-consistency-only",
            "devicePassIndependentlyProven": False,
            "disclaimer": DISCLAIMER,
            "error": f"{type(exc).__name__}: {exc}",
            "kind": "unexpected-error",
        }
    try:
        _write_output(args.output, failure)
    except EvidenceValidationError as exc:
        print(json.dumps({"passed": False, "error": f"{failure['error']}; {exc}"}, separators=(",", ":")))
        return 1
    print(json.dumps({"passed": False, "error": failure["error"]}, separators=(",", ":")))
    return 1


if __name__ == "__main__":
    sys.exit(main())
