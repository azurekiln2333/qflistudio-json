# Family offline host source audit — 2026-10-23

本报告记录对 `D:/MyNewProjects/qfli_{c,dart,go,java,json,lua,note,python,rust,sql,web}` 的只读源代码审查。范围是当前 OHOS manifest、EntryAbility 平台通道、Dart product profile，以及判断其正常 UI 可达性所需的共享策略和本机服务实现。审查时没有写入产品源码、操作进程、构建或访问任何设备。

这是 **source-only** 证据，不是抓包、实际联网、权限运行效果或设备安装包的证明。各仓库仍可能被其他会话修改；下面的路径和行号对应本次观察，不是十一产品共同的冻结提交或 HAP 指纹。没有 INTERNET 权限不等于委托外部浏览器的代码已消失；有 INTERNET 权限也不能独立证明产品依赖外网。

## Summary

十一产品均设置 `isOffline: true`。共享 `StudioProfile` 在 `lib/services/studio_profile.dart:118` 将 `offlineOnly` 默认设为 `isOffline`；这些产品均未显式选择 `offlineOnly: false`。它们的 pubspec 使用相邻的 `../qfli_studio_core`。

本次没有找到下表中账号或协议分支在正常离线启动时自动执行的证据。明确需要保留的区别是：

- C、Java、Note、Python、SQL 仍注册 Huawei login 原生处理器。
- C、Go、Java、Note、Python、Rust、SQL 仍注册远程 `openAgreement` 处理器及协议页面。
- Dart、Web 没有上述账号和协议处理器，但保留没有 URI/host 限定的原生 `openUrl`。
- JSON、Lua 对 `openAgreement` / `openUrl` 明确返回 `OFFLINE_ONLY`。
- 正常共享离线 UI 隐藏了账号、协议、云端、AI 和在线终端入口。这是当前界面及调用路径隔离，不能改写成“所有网络 API 已从包中移除”或“整个用户运行时都经过网络沙箱”。

## Product manifest, profile and native channels

下表路径以 `D:/MyNewProjects/` 为根。`manifest` 均为对应产品的 `ohos/entry/src/main/module.json5`；`EntryAbility` 均为 `ohos/entry/src/main/ets/entryability/EntryAbility.ets`。权限列列出整个 requestPermissions 区的当前权限，所有产品均保留 `READ_PASTEBOARD`。

| Product | Profile | Manifest permissions | EntryAbility facts |
| --- | --- | --- | --- |
| C | `qfli_c/lib/main.dart:42` — `isOffline: true` | `qfli_c/ohos/entry/src/main/module.json5:43` — INTERNET；`:45` — READ_PASTEBOARD | `qfli_c/ohos/entry/src/main/ets/entryability/EntryAbility.ets:67` — remote openAgreement；`:91` — arbitrary-URI openUrl；`:140` — Huawei login，`:150` — executeRequest |
| Dart | `qfli_dart/lib/main.dart:37` — `isOffline: true` | `qfli_dart/ohos/entry/src/main/module.json5:36` — requestPermissions；`:38` — READ_PASTEBOARD only | `qfli_dart/ohos/entry/src/main/ets/entryability/EntryAbility.ets:55` — openUrl without URI restriction；no Huawei/openAgreement handler |
| Go | `qfli_go/lib/main.dart:37` — `isOffline: true` | `qfli_go/ohos/entry/src/main/module.json5:37` — INTERNET；`:39` — READ_PASTEBOARD | `qfli_go/ohos/entry/src/main/ets/entryability/EntryAbility.ets:47` — remote openAgreement；`:65` — arbitrary-URI openUrl；no Huawei handler |
| Java | `qfli_java/lib/main.dart:41` — `isOffline: true` | `qfli_java/ohos/entry/src/main/module.json5:43` — INTERNET；`:45` — READ_PASTEBOARD | `qfli_java/ohos/entry/src/main/ets/entryability/EntryAbility.ets:51` — remote openAgreement；`:69` — arbitrary-URI openUrl；`:118` — Huawei login，`:128` — executeRequest |
| JSON | `qfli_json/lib/main.dart:30` — `isOffline: true` | `qfli_json/ohos/entry/src/main/module.json5:42` — requestPermissions；`:44` — READ_PASTEBOARD only | `qfli_json/ohos/entry/src/main/ets/entryability/EntryAbility.ets:47` — both openAgreement/openUrl rejected；`:48` — OFFLINE_ONLY；no Huawei handler |
| Lua | `qfli_lua/lib/main.dart:39` — `isOffline: true` | `qfli_lua/ohos/entry/src/main/module.json5:36` — requestPermissions；`:38` — READ_PASTEBOARD only | `qfli_lua/ohos/entry/src/main/ets/entryability/EntryAbility.ets:53` / `:55` — openAgreement rejected；`:64` / `:66` — openUrl rejected；no Huawei handler |
| Note | `qfli_note/lib/main.dart:33` — `isOffline: true` | `qfli_note/ohos/entry/src/main/module.json5:75` — INTERNET；`:76` — FILE_ACCESS_PERSIST；`:78` — READ_PASTEBOARD | `qfli_note/ohos/entry/src/main/ets/entryability/EntryAbility.ets:72` — remote openAgreement；`:82` — arbitrary-URI openUrl；`:131` — Huawei login，`:141` — executeRequest |
| Python | `qfli_python/lib/main.dart:33` — `isOffline: true` | `qfli_python/ohos/entry/src/main/module.json5:36` — requestPermissions；`:38` — READ_PASTEBOARD only | `qfli_python/ohos/entry/src/main/ets/entryability/EntryAbility.ets:58` — remote openAgreement；`:78` — arbitrary-URI openUrl；`:127` — Huawei login，`:137` — executeRequest |
| Rust | `qfli_rust/lib/main.dart:35` — `isOffline: true` | `qfli_rust/ohos/entry/src/main/module.json5:36` — requestPermissions；`:40` — READ_PASTEBOARD only | `qfli_rust/ohos/entry/src/main/ets/entryability/EntryAbility.ets:55` — remote openAgreement；`:65` — arbitrary-URI openUrl；no Huawei handler |
| SQL | `qfli_sql/lib/main.dart:30` — `isOffline: true` | `qfli_sql/ohos/entry/src/main/module.json5:43` — INTERNET；`:45` — READ_PASTEBOARD | `qfli_sql/ohos/entry/src/main/ets/entryability/EntryAbility.ets:66` — remote openAgreement；`:84` — arbitrary-URI openUrl；`:133` — Huawei login，`:143` — executeRequest |
| Web | `qfli_web/lib/main.dart:31` — `isOffline: true` | `qfli_web/ohos/entry/src/main/module.json5:37` — INTERNET；`:39` — READ_PASTEBOARD | `qfli_web/ohos/entry/src/main/ets/entryability/EntryAbility.ets:60` — openUrl without URI restriction；no Huawei/openAgreement handler |

这些仍注册的处理器是可以被同一 Flutter engine 的 Dart 平台通道调用的真实原生能力，不是“仅留下未使用的 import”。注册本身并不执行认证、加载协议或打开浏览器；没有发现当前正常离线 UI 会自动调用这些账号/协议分支。MethodChannel 也不能据此描述成其他应用可直接调用的公开网络接口。

## Shared UI and startup boundaries

以下路径以 `D:/MyNewProjects/qfli_studio_core/` 为根：

| Source | Observed boundary |
| --- | --- |
| `lib/services/studio_profile.dart:118` | `offlineOnly` defaults to `isOffline`；`:193` documents the network-entry hiding policy |
| `lib/pages/profile_page.dart:49` | Offline mode skips profile refresh；this line is not a guard inside the login method |
| `lib/pages/profile_page.dart:110` | Offline mode omits the account/login header and online blocks；`:209` omits admin entries；`:241` omits the external agreement footer |
| `lib/pages/profile_page.dart:69` | Settings are opened with AI disabled for offline products |
| `lib/pages/home_page.dart:335` | Offline products omit the cloud scope；`:348` avoids account activity refresh；`:811` returns before remote catalog refresh |
| `lib/editor/editor_page.dart:277` | Offline mode does not open cloud synchronization for a cloud project |
| `lib/editor/editor_page.dart:1512` | The fallback to an online runner is gated by offlineOnly；the terminal pane also receives the offline onlineEnabled setting |
| `lib/splash_screen.dart:99` | Bootstrap loads the local project/auth/settings stores |
| `lib/store/auth_store.dart:28` | Auth load reads local session state；it does not automatically call refreshMe |
| `lib/services/api_client.dart:129` | `ApiClient._send` has no offlineOnly rejection；`:143` sends the HTTP request |

The native leftovers and the shared API client therefore remain a policy-enforcement gap if a caller bypasses or later reintroduces a UI route. This source audit does not establish that such a route is currently reached, or that a request succeeds on a particular target. The shared code still supports a separate online product; its continued presence is not itself evidence of automatic networking by all offline products.

## AgreementReader source versus reachable route

- C、Go、Java、Note、Python、Rust、SQL：各自 `ohos/entry/src/main/resources/base/profile/main_pages.json:4` 仍注册 AgreementReader；对应 `ohos/entry/src/main/ets/pages/AgreementReader.ets:81` 真实创建 `Web({ src: this.url, ... })`。结合上表有效的 openAgreement 处理器，这些是原生可调用的远程协议能力；当前离线 UI 隐藏其入口。
- JSON：`qfli_json/ohos/entry/src/main/resources/base/profile/main_pages.json:4` 和 `qfli_json/ohos/entry/src/main/ets/pages/AgreementReader.ets:81` 仍存在，但 EntryAbility `:47` 拒绝进入。不能把这个用户原有页面源文件单独当成当前正常 UI 会打开网页的证据。
- Lua：AgreementReader 源文件仍在（`qfli_lua/ohos/entry/src/main/ets/pages/AgreementReader.ets:81`），但 `qfli_lua/ohos/entry/src/main/resources/base/profile/main_pages.json:3` 只注册 Index，且 EntryAbility 明确拒绝协议和 URL 方法。
- Web：AgreementReader 源文件仍在（`qfli_web/ohos/entry/src/main/ets/pages/AgreementReader.ets:81`），但 `qfli_web/ohos/entry/src/main/resources/base/profile/main_pages.json:3` 只注册 Index，EntryAbility 没有 openAgreement 分支。
- Dart：`qfli_dart/ohos/entry/src/main/resources/base/profile/main_pages.json:3` 只注册 Index，AgreementReader 源文件不存在，EntryAbility 也没有协议处理器。

## Local communication and product-specific controls

### Web: loopback preview is an actual product path

- `qfli_web/lib/services/web_dev_server.dart:36` produces a `http://127.0.0.1:$port/` URL；`:58` validates offline configuration；`:59` binds `InternetAddress.loopbackIPv4`.
- `qfli_web/lib/services/nginx_session.dart:72` validates the same configuration；`:337` emits `listen 127.0.0.1:$port`；`:340` emits the offline Content-Security-Policy header.
- `qfli_web/lib/pages/web_tools_page.dart:141` takes `_server?.url` and `:150` passes that current local URL to the native openUrl channel. The source proves this caller supplies a local preview URL; the native handler itself still has no repeated loopback allowlist.
- `qfli_web/lib/pages/web_tools_page.dart:37` hides the HTTP tool when offline；`:333` hides the external proxy editor.
- `qfli_web/lib/services/web_project_config.dart:47` validates all saved or directly supplied proxy targets；`:56` parses a literal IP and `:57` requires `isLoopback`, excluding DNS names, LAN addresses and ordinary external targets. The serving engines enforce this validation rather than relying only on hidden UI.
- `qfli_web/lib/services/web_project_config.dart:22` defines a local-resource CSP with `connect-src 'self'` and `form-action 'self'`; `web_dev_server.dart:127` sets it on responses. These source controls are not a packet or arbitrary system-browser navigation test.

The INTERNET permission cannot be rejected merely because this offline product runs a local web service and opens its local preview.

### Note: current document links and images reject remote resources

- `qfli_note/lib/workspace/workspace_actions.dart:142` classifies a clicked link；`:159` rejects remoteHttp/blocked navigation. `:195` only delegates resolved local-file URLs to an external opener.
- `qfli_note/lib/workspace/markdown_tools.dart:442` also rejects remote/blocked links in the standalone tool preview.
- `qfli_note/lib/markdown/md_preview_widgets.dart:8` resolves images only into MemoryImage or FileImage, not NetworkImage.
- `qfli_note/lib/markdown/md_resource_policy.dart:89` is the shared resource classifier；`:106` rejects protocol-relative/UNC paths；`:114` recognizes remote HTTP；`:124` rejects network-host file URIs.

These actual product paths prevent ordinary remote Markdown links/images from being loaded or opened. The broader native openUrl/account/agreement handlers in the table remain separate residual capabilities. Their presence and the manifest permission do not prove this current Markdown preview performs network requests.

### Java and the shared HTML preview: actual loopback sockets

- `qfli_java/lib/java_studio_debugger.dart:49` connects the debugger into the editor.
- `qfli_java/lib/java_debugger.dart:601` connects JDWP to `127.0.0.1`；`:1333` makes the helper listen only on that address.
- `qfli_studio_core/lib/services/local_web_server.dart:54` produces a local preview URL；`:74` binds loopbackIPv4. `qfli_studio_core/lib/editor/editor_page.dart:1422` begins the HTML preview path.

These local service/debugger paths must be distinguished from a dependency on an external website or cloud execution service.

### SQL: current MySQL transport is a private Unix socket

- `qfli_sql/ohos/entry/src/main/ets/plugins/QfliMysqlRuntime.ets:140` uses `${root}/mysql.sock`；`:781` writes `skip-networking` into the server configuration.
- `qfli_sql/native/src/qfli_mysql_client.cpp:111` selects `MYSQL_PROTOCOL_SOCKET` on the relevant non-Windows path；`:142` passes `localhost` with port zero and `:144` passes the explicit socket path. The localhost string alone is not evidence of TCP loopback.
- `qfli_sql/lib/sql_engine_preference.dart:29` disables cloud engines for offline profiles；`:84` refuses saving a cloud selection.
- `qfli_sql/lib/sql_workbench_page.dart:141` replaces a stale cloud setting with a local engine；`:236` refuses switching to cloud while offline.

The inspected MySQL path does not support a claim that TCP INTERNET permission is required for that transport. The permission still does not independently demonstrate external access.

## User-program capability is a separate boundary

Go's offline product UI and local interpreter do not imply a network sandbox for authored Go programs. `qfli_go/native/go_runtime/runtime.go:250` loads `stdlib.Symbols`; `qfli_go/native/go_runtime/vendor/github.com/traefik/yaegi/stdlib/go1_22_net.go:21` exposes native Dial, and `qfli_go/native/go_runtime/vendor/github.com/traefik/yaegi/stdlib/go1_22_net_http.go:56` exposes native Get. No target-address restriction was found in that mapping. This is a source-level capability available to a user who actively runs such code, not evidence that the app automatically contacts those hosts or that a device request was tested.

Dart has a different explicit boundary: `qfli_dart/lib/dart_runner.dart:368` uses the portable interpreter on OHOS, while `qfli_dart/vendor/tom_d4rt/lib/src/security/offline_host_policy.dart:53` rejects network-class permissions. This statement describes that policy source; this review did not run the interpreter or claim equivalent sandboxing for every other language.

## Limits

This review identifies source-level native capability, current UI gating and concrete local transports. It does not prove zero packets, successful or failed external requests under OHOS permissions, runtime enforcement on a physical device, equivalence to an installed HAP, or completeness of every possible authored-program call path. No new build, source fix, permission removal, process action or device operation was performed for this audit.
