# FinTrack restore safety audit

Before replacing persisted finance data, validate backup format version, unique identifiers across all ten collections, and all UUID relationships. Invalid backups must leave the existing SwiftData store unchanged.

Current P0 issue: `BackupManager.restore` calls `wipeAll`, which saves deletions before import completes; it then saves inserts and a balance recalculation separately. A failure can therefore leave a partial or empty database.

Required tests on a disposable in-memory SwiftData store: reject unsupported versions; reject duplicate IDs and missing references without mutation; preserve original records when any import or save step fails; verify full round-trip after successful import. Do not merge until these checks pass in macOS XCTest. Never test against personal financial data.
