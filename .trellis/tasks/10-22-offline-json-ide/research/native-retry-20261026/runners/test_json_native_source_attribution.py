"""Pure filesystem controls for isolated Flutter source attribution. No SDK."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "lib/json/json_verification_page.dart").is_file())
MODULE = Path(__file__).with_name("inspect_json_release_hap.py")
if not MODULE.is_file():
    MODULE = ROOT / ".trellis/.runtime/inspect_json_release_hap.py"
spec = importlib.util.spec_from_file_location("native_inspector", MODULE)
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


def signature(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def escaped(path):
    return str(path.resolve()).replace("\\", "\\\\").replace(" ", "\\ ")


class SourceAttributionTests(unittest.TestCase):
    def setUp(self):
        (ROOT / "build").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="attribution-control-", dir=ROOT / "build")
        self.addCleanup(self.temp.cleanup)
        self.staging = Path(self.temp.name)
        self.app = self.staging / "qfli_json"
        self.core = self.staging / "qfli_studio_core"
        self.plugin = self.staging / "native_plugins/path_provider_ohos"
        self.inputs = [self.app / "lib/main.dart", self.core / "lib/services/studio_profile.dart",
                       self.core / "vendor/re_editor/lib/re_editor.dart", self.plugin / "LICENSE",
                       self.plugin / "lib/path_provider_ohos.dart"]
        for i, path in enumerate(self.inputs):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("source " + str(i), encoding="utf-8")
        self.build = self.app / ".dart_tool/flutter_build/control"
        self.build.mkdir(parents=True)
        self.kernel = self.build / "kernel_blob.bin"
        self.kernel.write_bytes(b"synthetic kernel identity")
        self.dill = self.build / "app.dill"
        self.dill.write_bytes(self.kernel.read_bytes())
        self.kernel_hash = signature(self.kernel)["sha256"]
        self.config = {"configVersion": 2, "packages": [
            {"name": "qfli_json", "rootUri": self.app.as_uri() + "/"},
            {"name": "qfli_studio_core", "rootUri": self.core.as_uri() + "/"},
            {"name": "re_editor", "rootUri": (self.core / "vendor/re_editor").as_uri() + "/"},
            {"name": "path_provider_ohos", "rootUri": self.plugin.as_uri() + "/"},
        ]}
        self.write_config()
        self.app.joinpath(".flutter-plugins-dependencies").write_text(json.dumps({
            "plugins": {"ohos": [{"name": "path_provider_ohos", "path": str(self.plugin) + "/"}]}
        }), encoding="utf-8")
        self.prepared = {"appRoot": str(self.app), "coreRoot": str(self.core), "files": {
            "nativePlugins/" + path.relative_to(self.staging / "native_plugins").as_posix(): signature(path)
            for path in self.inputs if path.is_relative_to(self.plugin)
        }}
        self.write_depfiles()

    def write_config(self):
        self.app.joinpath(".dart_tool/package_config.json").write_text(json.dumps(self.config), encoding="utf-8")

    def write_depfiles(self, aggregate=None, compiler=None):
        aggregate = self.inputs if aggregate is None else aggregate
        compiler = self.inputs if compiler is None else compiler
        for name, output, inputs in [("flutter_build.d", self.kernel, aggregate),
                                     ("kernel_snapshot_program.d", self.dill, compiler)]:
            (self.build / name).write_text(escaped(output) + ": " + " ".join(map(escaped, inputs)) + "\n", encoding="utf-8")

    def check(self, prepared=True):
        return inspector.source_dependencies(self.app, self.core, self.kernel_hash,
                                             self.prepared if prepared else None)

    def test_accept_exact_frozen_isolated_plugin_files(self):
        result = self.check()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["isolatedNativePlugins"]["preparedManifestVerified"])

    def test_missing_prepared_manifest_refuses_native_inputs(self):
        with self.assertRaises(inspector.BlockedInspection):
            self.check(prepared=False)

    def test_wrong_prepared_app_root_is_rejected(self):
        self.prepared["appRoot"] = str(ROOT)
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_wrong_prepared_core_root_is_rejected(self):
        self.prepared["coreRoot"] = str(ROOT.parent / "qfli_studio_core")
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_undeclared_plugin_input_is_rejected(self):
        del self.prepared["files"]["nativePlugins/path_provider_ohos/LICENSE"]
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_changed_plugin_hash_is_rejected(self):
        self.inputs[-1].write_text("changed after capture", encoding="utf-8")
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_changed_plugin_byte_count_is_rejected(self):
        self.prepared["files"]["nativePlugins/path_provider_ohos/LICENSE"]["bytes"] += 1
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_original_live_app_dependency_is_rejected(self):
        self.write_depfiles(aggregate=self.inputs + [ROOT / "lib/main.dart"])
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_other_staging_dependency_is_rejected(self):
        foreign = self.staging.parent / "different-staging/native_plugins/path_provider_ohos/LICENSE"
        self.write_depfiles(aggregate=self.inputs + [foreign])
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_original_live_core_dependency_is_rejected(self):
        foreign = ROOT.parent / "qfli_studio_core/lib/services/studio_profile.dart"
        self.write_depfiles(compiler=self.inputs + [foreign])
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_compiler_source_must_appear_in_aggregate(self):
        self.write_depfiles(aggregate=self.inputs[1:])
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_package_config_must_name_exact_core(self):
        self.config["packages"][1]["rootUri"] = (ROOT.parent / "qfli_studio_core").as_uri() + "/"
        self.write_config()
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_plugin_package_mapping_must_match_capture(self):
        self.config["packages"][3]["rootUri"] = (self.staging / "rogue").as_uri() + "/"
        self.write_config()
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_plugin_metadata_must_match_capture(self):
        self.app.joinpath(".flutter-plugins-dependencies").write_text(json.dumps({
            "plugins": {"ohos": [{"name": "path_provider_ohos", "path": str(self.staging / "rogue")}]}
        }), encoding="utf-8")
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_depfile_keeps_spelled_input_paths(self):
        data = inspector.parse_depfile(self.build / "flutter_build.d")
        self.assertEqual(data["inputPaths"], [p.absolute() for p in self.inputs])
        self.assertEqual(len(data["inputPaths"]), len(data["inputs"]))

    def test_plugin_link_escape_outside_snapshot_is_rejected(self):
        original = inspector.parse_depfile
        foreign = Path(tempfile.gettempdir()) / "foreign-json-compile-source.dart"
        spelled = self.plugin / "lib/escaped-source.dart"
        def redirected(path):
            result = original(path)
            if Path(path).name == "flutter_build.d":
                result["inputs"].append(foreign.resolve())
                result["inputPaths"].append(spelled.absolute())
            return result
        with patch.object(inspector, "parse_depfile", side_effect=redirected):
            with self.assertRaises(inspector.BlockedInspection):
                self.check()

    def test_declared_plugin_must_appear_in_compiler_evidence(self):
        self.write_depfiles(aggregate=self.inputs[:3], compiler=self.inputs[:3])
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_native_compiler_source_must_appear_in_aggregate(self):
        self.write_depfiles(aggregate=self.inputs[:-1])
        with self.assertRaises(inspector.BlockedInspection):
            self.check()

    def test_missing_compiler_depfile_is_rejected(self):
        (self.build / "kernel_snapshot_program.d").unlink()
        with self.assertRaises(inspector.BlockedInspection):
            self.check()


if __name__ == "__main__":
    unittest.main(verbosity=2)
