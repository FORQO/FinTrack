"""Fail-closed SwiftData backup export for pinned Mint Leaf 4.2 sources.

CI checks out the original upstream code, so changing only a checked-in Swift
copy is insufficient. Refuse unknown layouts rather than producing unsafe builds.
"""
from pathlib import Path

MODELS = {
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
}

OLD_HELPER = """        func fetch<T: PersistentModel>(_ type: T.Type) -> [T] {
            (try? context.fetch(FetchDescriptor<T>())) ?? []
        }"""
NEW_HELPER = """        // FINTRACK BACKUP GUARD: Never turn a failed query into empty backup data.
        func fetch<T: PersistentModel>(_ type: T.Type) throws -> [T] {
            try context.fetch(FetchDescriptor<T>())
        }"""

OLD_DECODE = "        let backup = try decoder.decode(MintLeafBackup.self, from: data)"
NEW_DECODE = """        let backup = try decoder.decode(MintLeafBackup.self, from: data)
        // Refuse unknown schemas before deleting any existing financial records.
        guard backup.formatVersion == 1 else {
            throw FinTrackBackupValidationError.unsupportedFormat(backup.formatVersion)
        }"""

ERROR_DECLARATION = """// FINTRACK BACKUP GUARD: Reject incompatible backup formats.
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


def transform(source: str) -> str:
    """Apply exactly one safe transformation or reject unfamiliar upstream code."""
    if OLD_HELPER in source:
        if source.count(OLD_HELPER) != 1 or NEW_HELPER in source:
            raise RuntimeError("Unexpected backup export fetch helper")
        source = source.replace(OLD_HELPER, NEW_HELPER, 1)
    elif source.count(NEW_HELPER) != 1:
        raise RuntimeError("Unknown backup export fetch implementation")

    for model, name in MODELS.items():
        old = f"let {name} = fetch({model}.self)"
        new = f"let {name} = try fetch({model}.self)"
        if old in source:
            if source.count(old) != 1 or new in source:
                raise RuntimeError(f"Unexpected backup export query: {model}")
            source = source.replace(old, new, 1)
        elif source.count(new) != 1:
            raise RuntimeError(f"Missing expected backup export query: {model}")

    if NEW_DECODE in source:
        if source.count(NEW_DECODE) != 1:
            raise RuntimeError("Duplicate backup format validation")
    elif source.count(OLD_DECODE) == 1:
        source = source.replace(OLD_DECODE, NEW_DECODE, 1)
    else:
        raise RuntimeError("Unknown backup restore decode implementation")

    if ERROR_DECLARATION not in source:
        marker = "// MARK: - Backup Manager\n"
        if source.count(marker) != 1:
            raise RuntimeError("Unknown backup manager declaration")
        source = source.replace(marker, ERROR_DECLARATION + marker, 1)
    elif source.count(ERROR_DECLARATION) != 1:
        raise RuntimeError("Duplicate backup validation error declaration")

    return source


def patch(root: Path, rewrite):
    path = root / "MintLeaf/Services/BackupManager.swift"
    if not path.is_file():
        raise RuntimeError("Missing BackupManager.swift; refusing unsafe patch")
    return rewrite(path, transform)
