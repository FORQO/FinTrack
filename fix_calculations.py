"""Surgical fixes for mixed-currency totals in the upstream analytics screens.

All conversions happen at display/aggregation time; raw transactions and account
balances remain unchanged. Unsupported historical currencies can still be read.
"""
from pathlib import Path


def patch(root: Path, rewrite):
    changed = 0
    def replace_all(rel, pairs):
        nonlocal changed
        file = root / rel
        def run(src):
            for old, new in pairs:
                if old not in src and new not in src:
                    raise RuntimeError(f"Unexpected upstream version: {rel} missing {old[:80]!r}")
                src = src.replace(old, new)
            return src
        changed += rewrite(file, run)

    # SwiftUI NetWorth screen: every asset, liability, graph point uses same base.
    helper = '''    @AppStorage("defaultCurrency") private var fintrackCurrency = "RUB"
    private func inBase(_ amount: Decimal, account: Account) -> Decimal {
        ExchangeRateService.shared.convert(amount, from: account.currency, to: fintrackCurrency)
    }

'''
    f = root / "MintLeaf/Views/Trends/NetWorthView.swift"
    def networth(src):
        if "private func inBase(" in src: return src
        src = src.replace('    @State private var timeRange:', helper + '    @State private var timeRange:', 1)
        src = src.replace('$0 + $1.currentBalance', '$0 + inBase($1.currentBalance, account: $1)')
        src = src.replace('$0 + abs($1.currentBalance)', '$0 + abs(inBase($1.currentBalance, account: $1))')
        src = src.replace('for (_, bal) in balances {\n            if bal > 0', 'for (account, rawBalance) in balances {\n            let bal = inBase(rawBalance, account: account)\n            if bal > 0')
        src = src.replace('CurrencyFormatter.shared.format(account.currentBalance)',
                          'CurrencyFormatter.shared.format(account.currentBalance, currency: account.currency)')
        src = src.replace('CurrencyFormatter.shared.format(abs(account.currentBalance))',
                          'CurrencyFormatter.shared.format(abs(account.currentBalance), currency: account.currency)')
        src = src.replace('$0.currentBalance > $1.currentBalance',
                          'inBase($0.currentBalance, account: $0) > inBase($1.currentBalance, account: $1)')
        src = src.replace('$0.currentBalance < $1.currentBalance',
                          'inBase($0.currentBalance, account: $0) < inBase($1.currentBalance, account: $1)')
        return src
    changed += rewrite(f, networth)

    # Trends calculations: sum the converted amounts, not mixed native units.
    t = root / "MintLeaf/Views/Trends/TrendsView.swift"
    def trends(src):
        if "private func amountInBase(" in src: return src
        helper = '''    @AppStorage("defaultCurrency") private var fintrackCurrency = "RUB"
    private func amountInBase(_ tx: Transaction) -> Decimal {
        ExchangeRateService.shared.convert(tx.amount,
            from: tx.account?.currency ?? fintrackCurrency, to: fintrackCurrency)
    }
    private func accountBase(_ amount: Decimal, _ account: Account) -> Decimal {
        ExchangeRateService.shared.convert(amount, from: account.currency, to: fintrackCurrency)
    }

'''
        src = src.replace('    @State private var timeRange:', helper + '    @State private var timeRange:', 1)
        src = src.replace('reduce(Decimal.zero) { $0 + $1.amount }',
                          'reduce(Decimal.zero) { $0 + amountInBase($1) }')
        src = src.replace('reduce(Decimal.zero) { $0 + abs($1.amount) }',
                          'reduce(Decimal.zero) { $0 + abs(amountInBase($1)) }')
        src = src.replace('accounts.reduce(Decimal.zero) { $0 + $1.initialBalance }',
                          'accounts.reduce(Decimal.zero) { $0 + accountBase($1.initialBalance, $1) }')
        src = src.replace('running += txn.amount', 'running += amountInBase(txn)')
        return src
    changed += rewrite(t, trends)

    # Reports: all categories, merchants, single-account totals in base currency.
    f = root / "MintLeaf/Views/Trends/ReportsView.swift"
    def reports(src):
        if 'private func fintrackBase(' in src: return src
        helper = '''    @AppStorage("defaultCurrency") private var fintrackCurrency = "RUB"
    private func fintrackBase(_ tx: Transaction) -> Decimal {
        ExchangeRateService.shared.convert(tx.amount,
            from: tx.account?.currency ?? fintrackCurrency, to: fintrackCurrency)
    }

'''
        src = src.replace('    @Environment(\\.colorScheme) private var scheme',
                          '    @Environment(\\.colorScheme) private var scheme\n' + helper, 1)
        src = src.replace('reduce(Decimal.zero) { $0 + $1.amount }',
                          'reduce(Decimal.zero) { $0 + fintrackBase($1) }')
        src = src.replace('reduce(Decimal.zero) { $0 + abs($1.amount) }',
                          'reduce(Decimal.zero) { $0 + abs(fintrackBase($1)) }')
        src = src.replace('+= abs(txn.amount)', '+= abs(fintrackBase(txn))')
        return src
    changed += rewrite(f, reports)

    # Forecast & insights: the source forecast model must use converted values too.
    f = root / "MintLeaf/Services/CashflowForecaster.swift"
    def forecaster(src):
        if "private static func inPreferredCurrency(" in src: return src
        src = src.replace('final class CashflowForecaster {', '''final class CashflowForecaster {
    private static func inPreferredCurrency(_ tx: Transaction) -> Decimal {
        ExchangeRateService.shared.convert(tx.amount,
            from: tx.account?.currency ?? "RUB", to: ExchangeRateService.shared.preferredCurrency)
    }
    private static func inPreferredCurrency(_ scheduled: ScheduledTransaction) -> Decimal {
        ExchangeRateService.shared.convert(scheduled.amount,
            from: scheduled.currency, to: ExchangeRateService.shared.preferredCurrency)
    }
''', 1)
        src = src.replace('$0 + abs($1.amount)', '$0 + abs(inPreferredCurrency($1))')
        src = src.replace('$0 + $1.amount', '$0 + inPreferredCurrency($1)')
        src = src.replace('dayAmount += scheduled.amount', 'dayAmount += inPreferredCurrency(scheduled)')
        return src
    changed += rewrite(f, forecaster)

    for rel in ('MintLeaf/Views/ForecastView.swift', 'MintLeaf/Views/Trends/InsightsView.swift'):
        f = root / rel
        def summary(src):
            if "private func fintrackBaseBalance(" in src: return src
            src = src.replace('    @Environment(\\.colorScheme) private var scheme', '''    @Environment(\\.colorScheme) private var scheme
    @AppStorage("defaultCurrency") private var fintrackCurrency = "RUB"
    private func fintrackBaseBalance(_ account: Account) -> Decimal {
        ExchangeRateService.shared.convert(account.currentBalance,
            from: account.currency, to: fintrackCurrency)
    }
''', 1)
            src = src.replace('reduce(Decimal.zero) { $0 + $1.currentBalance }',
                              'reduce(Decimal.zero) { $0 + fintrackBaseBalance($1) }')
            if rel.endswith('ForecastView.swift'):
                src = src.replace('CurrencyFormatter.shared.format(item.amount)',
                                  'CurrencyFormatter.shared.format(item.amount, currency: item.currency)')
                src = src.replace('reduce(Decimal.zero) { $0 + abs($1.monthlyEquivalent) }',
                  'reduce(Decimal.zero) { $0 + abs(ExchangeRateService.shared.convert($1.monthlyEquivalent, from: $1.currency, to: fintrackCurrency)) }')
                src = src.replace('reduce(Decimal.zero) { $0 + $1.monthlyEquivalent }',
                  'reduce(Decimal.zero) { $0 + ExchangeRateService.shared.convert($1.monthlyEquivalent, from: $1.currency, to: fintrackCurrency) }')
            return src
        changed += rewrite(f, summary)
    return changed