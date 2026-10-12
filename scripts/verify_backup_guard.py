#!/usr/bin/env python3
"""CI check: the generated Swift source must include the backup safety patch."""
import sys
from pathlib import Path

MODELS = (
    ("Account", "accounts"), ("Category", "categories"),
    ("Transaction", "transactions"), ("Budget", "budgets"),
    ("BudgetItem", "budgetItems"), ("ScheduledTransaction", "scheduled"),
    ("CategoryRule", "rules"), ("MerchantAlias", "aliases"),
    ("Goal", "goals"), ("Tag", "tags"),
)


def audit_source(src: str) -> None:
    start = src.find("static func export(context: ModelContext) throws -> Data")
    end = src.find("static func restore(from data: Data, context: ModelContext) throws -> Summary")
    if start < 0 or end <= start:
        raise RuntimeError("Unexpected Swift export/restore layout")
    exported = src[start:end]
    if exported.count("func fetch<T: PersistentModel>(_ type: T.Type) throws -> [T]") != 1:
        raise RuntimeError("Backup fetch errors must propagate")
    if exported.count("try context.fetch(FetchDescriptor<T>())") != 1:
        raise RuntimeError("Backup exporter lacks a throwing SwiftData fetch")
    if "(try? context.fetch(FetchDescriptor<T>())) ?? []" in exported:
        raise RuntimeError("Backup exporter still hides fetch errors")
    for model, name in MODELS:
        if exported.count(f"let {name} = try fetch({model}.self)") != 1:
            raise RuntimeError(f"Missing guarded query for {model}")
    restored = src[end:]
    decoded = restored.find("let backup = try decoder.decode(MintLeafBackup.self, from: data)")
    guarded = restored.find("guard backup.formatVersion == 1")
    rejected = restored.find("throw FinTrackBackupValidationError.unsupportedFormat(backup.formatVersion)")
    wiped = restored.find("try wipeAll(context: context)")
    if min(decoded, guarded, rejected, wiped) < 0 or not (decoded < guarded < rejected < wiped):
        raise RuntimeError("Backup schema version not checked before destructive restore")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: verify_backup_guard.py <generated BackupManager.swift>")
    try:
        audit_source(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (RuntimeError, OSError) as error:
        sys.exit(f"::error::Backup safety audit failed: {error}")
    print("Backup safety audit passed")


if __name__ == "__main__":
    main()
