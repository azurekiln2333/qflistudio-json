# Official contracts and offline choices

Reviewed 2026-10-22. Official editor and validation pages were fetched successfully (HTTP 200) using the host research client; application code has no research/network dependency.

| Primary source | Applicable contract / product choice |
| --- | --- |
| https://code.visualstudio.com/docs/languages/json | JSON editing, formatting, diagnostics, outline and schema assistance motivate local format/check, structure navigation and Problems. Remote schema download is excluded from the offline product. |
| https://www.jetbrains.com/help/idea/json.html | JSON syntax/format validation and schema assistance inform direct useful tools and navigable diagnostics; no claim of full IntelliJ completion/refactoring parity. |
| https://www.rfc-editor.org/rfc/rfc6901 | Pointer tokens decode ~1 and ~0, empty pointer selects root, array indexing is strict, missing differs from null. |
| https://www.rfc-editor.org/rfc/rfc6902 | Ordered add/remove/replace/move/copy/test, deep comparison, invalid paths and moving a node into its descendant; patch failure never mutates the source object. Removing the whole document is explicitly unsupported. |
| https://www.rfc-editor.org/rfc/rfc7396 | Object null members delete fields, other values including arrays replace; tested against examples. |
| https://json-schema.org/draft/2020-12/json-schema-validation | Explicitly scoped local subset. Types/constraints/combinators, local refs and metadata validation; unsupported keywords, dialects, external refs and nested resources return errors. Pattern uses Dart Unicode regex and a killable worker deadline. |

## Product boundaries

JSON is data, so useful execution means actual parsing, checking and formatted output. It has no statement execution or genuine breakpoints. Problems, local output and sandbox terminal commands are implemented. Debug Console/Ports and network module managers are not fabricated for JSON. C/C++ header resolution and Python modules/pip retain their independent runtime requirements in the umbrella task.

Tools are sixteen separate cards in the existing ToolsGrid. A card opens its actual operation; there is no extra product-feature hub. The normal CodeEditor receives diagnostics without requiring users to open the separate document workspace.
