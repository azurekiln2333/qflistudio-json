"""No-SDK controls for readiness changes before the first native build."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "lib/json/json_verification_page.dart").is_file())
MODULE = Path(__file__).with_name("prepare_json_ohos_inputs.py")
if not MODULE.is_file():
    MODULE = ROOT / ".trellis/.runtime/prepare_json_ohos_inputs.py"
spec = importlib.util.spec_from_file_location("native_prepare", MODULE)
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="json-readiness-control-", dir=ROOT / "build")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.runner = self.folder / "runner.py"
        self.runner.write_text("print('frozen')", encoding="utf-8")
        identity = prepare.signature(self.runner)
        self.commands = {
            "harness": {"executable": "hvigorw.bat", "cwd": "isolated/ohos", "arguments": ["DART_DEFINES=true", "ohos-x64"]},
            "normal": {"executable": "hvigorw.bat", "cwd": "isolated/ohos", "arguments": ["DART_DEFINES=", "ohos-x64"]},
        }
        self.actual = {
            "appRoot": "isolated/qfli_json", "coreRoot": "isolated/qfli_studio_core",
            "hostManifest": "passed/manifest.json", "hostManifestIdentity": {"bytes": 20, "sha256": "a" * 64},
            "coreCommit": "b" * 40, "coreTree": "c" * 40, "hostAppCommit": "d" * 40, "hostAppOverlays": {},
            "packageRoots": {"qfli_json": "isolated/qfli_json", "qfli_studio_core": "isolated/qfli_studio_core"},
            "files": {"app/lib/main.dart": identity, "app/ohos/oh-package-lock.json5": identity},
            "cacheReferences": {"plugin/oh_modules/flutter": "isolated/cache/flutter"},
            "originalExecutableComparison": {"main.dart": identity}, "originalAppInputs": {"ohos/profile": identity},
            "originalCacheReferences": {}, "tools": {"python": {"path": "python.exe", **identity}},
            "helperIdentity": identity, "exclusionPolicy": ["build"], "embeddedSigningConfigurationCopied": True,
            "buildParameters": {mode + ".command": json.dumps(command) for mode, command in self.commands.items()},
        }
        self.expected = copy.deepcopy(self.actual)
        self.expected.update({"prepared": True, "runners": {"runner": {"path": str(self.runner), **identity}},
                              "nativeCommands": copy.deepcopy(self.commands)})

    def check(self):
        return prepare.readiness_mismatches(self.expected, self.actual)

    def test_exact_ready_capture_passes(self):
        self.assertEqual(self.check(), [])

    def test_changed_lock_bytes_refuse_readiness(self):
        self.actual["files"]["app/ohos/oh-package-lock.json5"] = {"bytes": 21, "sha256": "e" * 64}
        self.assertIn("files", self.check())

    def test_added_native_input_refuses_readiness(self):
        self.actual["files"]["nativePlugins/plugin/extra.so"] = {"bytes": 3, "sha256": "f" * 64}
        self.assertIn("files", self.check())

    def test_cache_reference_change_refuses_readiness(self):
        self.actual["cacheReferences"]["plugin/oh_modules/flutter"] = "outside/cache"
        self.assertIn("cacheReferences", self.check())

    def test_existing_tool_hash_change_refuses_readiness(self):
        self.actual["tools"]["python"]["sha256"] = "0" * 64
        self.assertIn("tools", self.check())

    def test_added_tool_refuses_readiness(self):
        self.actual["tools"]["new"] = {"path": "new.exe", "bytes": 3, "sha256": "1" * 64}
        self.assertIn("tools", self.check())

    def test_runner_file_change_refuses_readiness(self):
        self.runner.write_text("print('changed')", encoding="utf-8")
        self.assertIn("runner/runner", self.check())

    def test_missing_runner_file_refuses_readiness(self):
        self.runner.unlink()
        self.assertIn("runner/runner", self.check())

    def test_harness_define_change_refuses_readiness(self):
        command = copy.deepcopy(self.commands["harness"])
        command["arguments"][0] = "DART_DEFINES=false"
        self.actual["buildParameters"]["harness.command"] = json.dumps(command)
        self.assertIn("command/harness", self.check())

    def test_normal_architecture_change_refuses_readiness(self):
        command = copy.deepcopy(self.commands["normal"])
        command["arguments"][1] = "ohos-arm64"
        self.actual["buildParameters"]["normal.command"] = json.dumps(command)
        self.assertIn("command/normal", self.check())

    def test_malformed_command_refuses_readiness(self):
        self.actual["buildParameters"]["normal.command"] = "not-json"
        self.assertIn("command/normal", self.check())

    def test_missing_reviewed_commands_refuses_readiness(self):
        self.expected.pop("nativeCommands")
        self.assertIn("missing-reviewed-native-commands", self.check())

    def test_core_revision_change_refuses_readiness(self):
        self.actual["coreCommit"] = "2" * 40
        self.assertIn("coreCommit", self.check())

    def test_helper_identity_change_refuses_readiness(self):
        self.actual["helperIdentity"] = {"bytes": 200, "sha256": "3" * 64}
        self.assertIn("helperIdentity", self.check())

    def test_unprepared_snapshot_refuses_readiness(self):
        self.expected["prepared"] = False
        self.assertIn("snapshot-not-prepared", self.check())

    def test_invalid_expected_document_refuses_readiness(self):
        self.assertEqual(prepare.readiness_mismatches([], self.actual), ["expected-prepared-not-object"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
