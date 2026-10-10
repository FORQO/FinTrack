import Foundation

struct CurrencyInfo: Identifiable {
    let code: String
    let name: String
    let flag: String
    var id: String { code }
}

enum SupportedCurrencies {
    static let all: [CurrencyInfo] = [
        CurrencyInfo(code: "RUB", name: "Российский рубль", flag: "🇷🇺"),
        CurrencyInfo(code: "USD", name: "Доллар США", flag: "🇺🇸"),
        CurrencyInfo(code: "EUR", name: "Евро", flag: "🇪🇺"),
    ]

    static func info(for code: String) -> CurrencyInfo? {
        all.first { $0.code == code }
    }
}

extension Array where Element: Hashable {
    func unique() -> [Element] {
        var seen = Set<Element>()
        return filter { seen.insert($0).inserted }
    }
}
