"""Fail-closed protection for Mint Leaf 4.2 backups.

The build fetches pinned upstream sources, so this patch is applied to the
upstream clone rather than only to the checked-in derived Swift source.
Do not silently accept an unfamiliar upstream implementation.
"""

from pathlib import Path


def patch(root: Path, rewrite):
    file = root / "MintLeaf/Services/BackupManager.swift"

    def transform(src: str) -> str:
        old_fetch = """        func fetch<T: PersistentModel>(_ type: T.Type) -> [T] {
            (try? context.fetch(FetchDescriptor<T>())) ?? []
        }"""
        new_fetch = """        // FINTRACK: Fail closed. A failed query must never turn into an empty backup.
        func fetch<T: PersistentModel>(_ type: T.Type) throws -> [T] {
            try context.fetch(FetchDescriptor<T>())
        }"""

        if old_fetch in src:
            if src.count(old_fetch) != 1:
                raise RuntimeError("Unexpected duplicate backup export fetch helpers")
            src = src.replace(old_fetch, new_fetch, 1)
        elif new_fetch not in src:
            raise RuntimeError("Unknown backup export fetch implementation")

        for model in (
            "Account", "Category", "Transaction", "Budget", "BudgetItem",
            "ScheduledTransaction", "CategoryRule", "MerchantAlias",
            "Goal", "Tag",
        ):
            old = f"let { _varname(model) } = fetch({model}.self)"
            new = f"let { _varname(model) } = try fetch({model}.self)"
            if old in src:
                if src.count(old) != 1:
                    raise RuntimeError(f"Unexpected export query count: {model}")
                src = src.replace(old, new, 1)
            elif new not in src:
                raise RuntimeError(f"Missing expected backup export query: {model}")

        old_decode = "        let backup = try decoder.decode(MintLeafBackup.self, from: data)"
        new_decode = """        let backup = try decoder.decode(MintLeafBackup.self, from: data)
        // FINTRACK: Validate the schema before any destructive restore operation.
        guard backup.formatVersion == 1 else {
            throw FinTrackBackupValidationError.unsupportedFormat(backup.formatVersion)
        }"""
        if new_decode in src:
            pass
        elif src.count(old_decode) == 1:
            src = src.replace(old_decode, new_decode, 1)
        else:
            raise RuntimeError("Unknown backup restore decode implementation")

        error_type = """// FINTRACK: Do not attempt to restore backups with unknown schemas.
enum FinTrackBackupValidationError: LocalizedError {
    case unsupportedFormat(Int)

    var errorDescription: String? {
        switch self {
        case .unsupportedFormat(let version):
            return "Неподдерживаемая версия резервной копии: \\(version)."
        }
    }
}

"""
        if error_type not in src:
            marker = "// MARK: - Backup Manager\n"
            if src.count(marker) != 1:
                raise RuntimeError("Cannot locate backup manager declaration")
            src = src.replace(marker, error_type + marker, 1)

        return src

    return rewrite(file, transform)


def _varname(model: str) -> str:
    return {
        "Account": "accounts",
        "Category": "categories",
        "Transaction": "transactions",
        "Budget": "budgets",
        "BudgetItem": "budgetItems",
        "ScheduledTransaction": "scheduled",
        "CategoryRule": "rules",
        "MerchantAlias": "aliases",
        "Goal": "goals",
        "Tag": "tags",
    }[model]
