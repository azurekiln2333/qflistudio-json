# QFLIJson

[简体中文](README.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md)

QFLIJson 是離線 JSON 編輯器。產品在本機處理文件。

## 功能

- 編輯器提供 JSON 語法醒目提示。
- 編輯器用波浪線標記語法錯誤。
- 問題面板顯示錯誤的行號與欄號。
- 結構檢視顯示 JSON Pointer 路徑。
- 執行入口輸出格式化的 JSON。
- 工作區容納多個本機專案根目錄。
- 具名工作區儲存開啟檔案與游標位置。
- 檔案樹保留各根目錄的展開狀態。

產品內建 340 條範例與 340 條教學。新增內容各有 240 條。

新增內容分為 24 類。每類包含 10 條。
校驗入口檢查 440 條練習答案。
校驗入口檢查 340 個輸入樣本。
10 條示例包含補丁或合併結果。

工具頁直接提供 16 張卡片。

| 工具 | 用途 |
| --- | --- |
| 格式化與驗證 | 整理縮排。驗證語法與重複鍵。 |
| JSON 壓縮 | 刪除字串外的無意義空白。 |
| 遞迴鍵排序 | 排序物件鍵。保留陣列順序。 |
| JSON Pointer 查詢 | 擷取路徑對應的值。 |
| 結構差異 | 產生 JSON Patch。 |
| Merge Patch | 合併物件。用 null 刪除欄位。 |
| JSON Patch | 套用 add、remove、replace、move、copy、test。 |
| 展開路徑 | 產生保留容器類型的路徑清單。 |
| 還原路徑 | 從路徑清單還原文件。 |
| JSON Lines 轉陣列 | 將逐行 JSON 轉換為陣列。 |
| 陣列轉 JSON Lines | 將每個元素輸出為一行 JSON。 |
| 字串跳脫 | 將文字編碼為 JSON 字串。 |
| 字串還原 | 還原 JSON 字串。 |
| 物件陣列轉 CSV | 將物件陣列轉換為表格文字。 |
| 本機 Schema 驗證 | 驗證類型、欄位與約束。 |
| 結構統計 | 統計節點、類型、深度與位元組數。 |

## 使用

1. 開啟本機專案。
2. 開啟 `.json` 檔案。
3. 編輯 JSON。
4. 查看問題面板。
5. 點選問題項目定位錯誤。
6. 點選執行按鈕。
7. 查看輸出。

執行入口優先讀取 `data.json`。其次讀取 `src/data.json`。

使用獨立工具時，請依下列步驟操作。

1. 開啟工具頁。
2. 選擇工具卡片。
3. 輸入 JSON。
4. 依需求填寫第二份輸入。
5. 點選執行按鈕。

終端機提供下列唯讀指令。指令輸出不會覆寫原始檔。

```text
json check <file>
json format <file>
json minify <file>
json sort <file>
json stats <file>
json get <file> <JSON Pointer>
```

`json help` 列出終端命令。

| 輸入 | 結束碼 |
| --- | --- |
| 有效 JSON | 0 |
| 無效 JSON | 1 |
| 檔案缺失或路徑越界 | 127 |

專案設定可指定入口檔案。
命名工作區保存專案識別碼與最後路徑。

## 開發

本倉庫是獨立 Flutter 應用程式。它依賴兄弟倉庫 `qflistudio-core`。

兩個倉庫必須位於同一父目錄。

```text
checkout-parent/
  qflistudio-core/
  qfli_json/
```

`pubspec.yaml` 宣告 Dart 約束 `^3.11.5`。
編輯器依賴指向 `../qflistudio-core/vendor/re_editor`。

1. 安裝 Flutter SDK。
2. 檢出兄弟倉庫。
3. 進入本倉庫根目錄。
4. 解析依賴。

```text
flutter pub get
```

5. 啟動目標裝置上的應用程式。

```text
flutter run
```

OHOS 建置需要匹配的 Flutter OHOS 工具鏈。標準 Flutter SDK 不包含該工具鏈。
其他 Flutter 通道可能也能運作。

應用程式執行時不需要網路。首次開發環境可能需要下載依賴。
離線開發需預先準備 SDK 與依賴快取。

## 驗證

執行測試。

```text
flutter test
```

執行靜態分析。

```text
dart analyze lib test
```

驗證格式。

```text
dart format --output=none --set-exit-if-changed lib test
```

驗證內建內容。

```text
python tool/build_json_content.py --check
```

該指令驗證三份資源。它不會改寫資源。

啟動課程驗證入口。

```text
flutter run --dart-define=QFLI_VERIFY_CATALOG=true
```

入口驗證範例、練習答案、輸入樣本與工具。
每次驗證產生新的 `runId`。
報告寫入失敗會使本次驗證失敗。

現有驗證記錄如下。結果可能仍取決於平台與套件。

| 範圍 | 結果 |
| --- | --- |
| 2026-10-24 主機完整測試 | 124 項通過，並行數為 1。 |
| 同次靜態分析 | `lib` 與 `test` 沒有問題。 |
| 同次資源驗證 | 三份資源一致。 |
| 2026-10-22 OHOS 模擬器 | API 26 x86_64 通過 340 條範例。 |

歷史裝置結果可能不涵蓋後續共用核心修改。
目前版本的全量裝置通過也許尚未證實。
簽署發行與實體 ARM64 裝置仍缺少驗收證據。

主機證據見[驗證記錄](.trellis/tasks/10-22-offline-json-ide/research/host-20261024-published-core.md)。
主機測試不能證明裝置通過。

JSON 證據不涵蓋兄弟產品。

## Schema 邊界

本機 Schema 驗證支援 JSON Schema 2020-12 的子集。

- 類型規則包含 `type`、`enum`、`const`。
- 物件規則包含 `properties`、`required`、`additionalProperties`。
- 陣列規則包含 `items`、`prefixItems`、`uniqueItems`。
- 組合規則包含 `allOf`、`anyOf`、`oneOf`、`not`。
- 驗證器支援長度、數量與數值約束。
- `$ref` 僅接受 `#` 或 `#/` 開頭的文件內參照。
- `pattern` 使用 Dart Unicode 正規表示式。

驗證器拒絕不支援的關鍵字。驗證器不取得遠端 Schema。
`format`、條件規則與 `patternProperties` 暫不受支援。
巢狀資源宣告暫不受支援。

完整關鍵字清單見 [Schema 實作](lib/json/json_schema.dart)。
子集驗證通過不代表完整規格驗證通過。

## 限制

| 項目 | 上限或行為 |
| --- | --- |
| 輸入 | 2 Mi UTF-16 程式碼單元。 |
| 輸出 | 4 Mi UTF-16 程式碼單元。 |
| 文件深度 | 128 層。 |
| 值節點 | 50000 個。 |
| CSV 儲存格 | 200000 個。 |
| 補丁累計工作量 | 250000 個節點。 |
| 工具工作 | 5 秒後逾時。使用者可取消工作。 |
| 執行入口讀取 | 2 MiB UTF-8 位元組。 |

超出有號 64 位元範圍的整數必須寫成字串。
小數與指數使用有限 Dart 雙精度數。

編輯器診斷只涵蓋 `.json` 文件。產品不提供中斷點偵錯器。
文件中的 URL 僅作為資料。應用程式不開啟該 URL。

產品約定見 [JSON 離線規範](.trellis/spec/json-offline.md)。
