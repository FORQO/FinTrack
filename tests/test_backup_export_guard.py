"""Unit tests for fail-closed backup transformations; no user data."""
import tempfile
import unittest
from pathlib import Path
from backup_export_guard import MODELS, NEW_HELPER, ERROR_DECLARATION, transform, patch


def fixture():
    body = """import Foundation
import SwiftData
struct MintLeafBackup { let formatVersion: Int }
// MARK: - Backup Manager
enum BackupManager {
    static func export(context: ModelContext) throws -> Data {
        func fetch<T: PersistentModel>(_ type: T.Type) -> [T] {
            (try? context.fetch(FetchDescriptor<T>())) ?? []
        }
"""
    body += "".join(f"        let {name} = fetch({model}.self)\n" for model, name in MODELS.items())
    return body + """    }
    static func restore(from data: Data, context: ModelContext) throws {
        let backup = try decoder.decode(MintLeafBackup.self, from: data)
        try wipeAll(context: context)
    }
}
"""


class BackupExportGuardTests(unittest.TestCase):
    def test_every_model_fetch_propagates_errors(self):
        result = transform(fixture())
        self.assertEqual(result.count(NEW_HELPER), 1)
        self.assertNotIn("(try? context.fetch(FetchDescriptor<T>())) ?? []", result)
        for model, name in MODELS.items():
            self.assertEqual(result.count(f"let {name} = try fetch({model}.self)"), 1)

    def test_format_checked_before_destructive_wipe(self):
        result = transform(fixture())
        self.assertLess(result.index("guard backup.formatVersion == 1"),
                        result.index("try wipeAll(context: context)"))
        self.assertIn(ERROR_DECLARATION, result)

    def test_idempotent(self):
        once = transform(fixture())
        self.assertEqual(once, transform(once))

    def test_unknown_export_fetch_fails_closed(self):
        src = fixture().replace("(try? context.fetch(FetchDescriptor<T>())) ?? []", "[]")
        with self.assertRaises(RuntimeError):
            transform(src)

    def test_absent_collection_fails_closed(self):
        src = fixture().replace("let budgets = fetch(Budget.self)", "let budgets = []")
        with self.assertRaises(RuntimeError):
            transform(src)

    def test_duplicate_model_query_fails_closed(self):
        src = fixture().replace("let tags = fetch(Tag.self)",
                                "let tags = fetch(Tag.self)\n        let tags = fetch(Tag.self)")
        with self.assertRaises(RuntimeError):
            transform(src)

    def test_unrecognized_decode_fails_closed(self):
        src = fixture().replace("let backup = try decoder.decode(MintLeafBackup.self, from: data)",
                                "let backup = invalid")
        with self.assertRaises(RuntimeError):
            transform(src)

    def test_patches_expected_file_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "MintLeaf/Services/BackupManager.swift"
            path.parent.mkdir(parents=True)
            path.write_text(fixture(), encoding="utf-8")
            def rewrite(file, change):
                original = file.read_text(encoding="utf-8")
                result = change(original)
                if result == original:
                    return 0
                file.write_text(result, encoding="utf-8")
                return 1
            self.assertEqual(patch(root, rewrite), 1)
            self.assertEqual(patch(root, rewrite), 0)


if __name__ == "__main__":
    unittest.main()
