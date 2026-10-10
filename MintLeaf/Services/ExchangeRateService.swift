import Foundation
#if canImport(FoundationXML)
import FoundationXML
#endif

final class ExchangeRateService: Sendable {
    static let shared = ExchangeRateService()

    private static let cacheKey = "cachedExchangeRates"
    private static let fetchedAtKey = "exchangeRatesFetchedAt"

    // Fallback rates relative to USD (1 USD = X units of currency), used until the
    // first successful fetch and for currencies the ECB feed doesn't cover.
    private let fallbackRates: [String: Decimal] = [
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "CAD": 1.36,
        "AUD": 1.53,
        "NZD": 1.67,
        "JPY": 154.5,
        "CNY": 7.24,
        "INR": 83.5,
        "CHF": 0.88,
        "SEK": 10.45,
        "NOK": 10.6,
        "DKK": 6.87,
        "PLN": 3.98,
        "CZK": 23.2,
        "HUF": 362.0,
        "BRL": 4.97,
        "MXN": 17.15,
        "ARS": 850.0,
        "ZAR": 18.6,
        "KRW": 1320.0,
        "SGD": 1.34,
        "HKD": 7.82,
        "TWD": 31.5,
        "THB": 35.8,
        "MYR": 4.72,
        "PHP": 56.2,
        "IDR": 15700.0,
        "TRY": 32.4,
        "RUB": 91.5,
        "SAR": 3.75,
        "AED": 3.67,
        "ILS": 3.65,
        "EGP": 30.9,
        "NGN": 1550.0,
        "KES": 153.0,
        "CLP": 940.0,
        "COP": 3950.0,
        "PEN": 3.72,
    ]

    /// Live rates cached from the last successful fetch, overriding the fallback table.
    private var cachedRates: [String: Decimal] {
        guard let dict = UserDefaults.standard.dictionary(forKey: Self.cacheKey) as? [String: Double] else { return [:] }
        return dict.mapValues { Decimal($0) }
    }

    private func rate(for code: String) -> Decimal? {
        cachedRates[code] ?? fallbackRates[code]
    }

    /// Convert an amount from one currency to another
    func convert(_ amount: Decimal, from source: String, to target: String) -> Decimal {
        guard source != target else { return amount }
        let sourceRate = rate(for: source) ?? 1.0
        let targetRate = rate(for: target) ?? 1.0
        // Convert to USD first, then to target
        let inUSD = amount / sourceRate
        return inUSD * targetRate
    }

    /// Official Central Bank of Russia daily rates. USD and EUR are quoted in RUB.
    /// Do not mark offline/fallback estimates as fresh exchange rates.
    func refresh() async {
        if let last = UserDefaults.standard.object(forKey: Self.fetchedAtKey) as? Date,
           Calendar.current.isDateInToday(last),
           cachedRates["RUB"] != nil, cachedRates["EUR"] != nil {
            return
        }
        guard let url = URL(string: "https://www.cbr.ru/scripts/XML_daily.asp") else { return }
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            guard (response as? HTTPURLResponse)?.statusCode == 200 else { return }
            let reader = FinTrackCBRRateReader()
            let parser = XMLParser(data: data)
            parser.delegate = reader
            guard parser.parse(),
                  let dollarInRubles = reader.rates["USD"],
                  let euroInRubles = reader.rates["EUR"],
                  dollarInRubles > 0, euroInRubles > 0 else { return }
            var newRates = cachedRates.mapValues { NSDecimalNumber(decimal: $0).doubleValue }
            newRates["USD"] = 1
            newRates["RUB"] = dollarInRubles
            newRates["EUR"] = dollarInRubles / euroInRubles
            UserDefaults.standard.set(newRates, forKey: Self.cacheKey)
            UserDefaults.standard.set(Date(), forKey: Self.fetchedAtKey)
            NotificationCenter.default.post(name: Notification.Name("FinTrackExchangeRatesUpdated"), object: nil)
        } catch {
            // Offline or CBR unavailable. Keep cached/fallback values and show
            // the dashboard's stale-rate warning instead of claiming freshness.
        }
    }
    /// Get the user's preferred currency
    var preferredCurrency: String {
        UserDefaults.standard.string(forKey: "defaultCurrency") ?? "RUB"
    }

    /// Format an amount converted to the user's preferred currency
    func formatConverted(_ amount: Decimal, from source: String) -> String {
        let converted = convert(amount, from: source, to: preferredCurrency)
        return CurrencyFormatter.shared.format(converted)
    }
}

// The official CBR feed is XML; values use comma decimals and may quote more
// than one unit of the source currency (Nominal). Both must be parsed.
final class FinTrackCBRRateReader: NSObject, XMLParserDelegate {
    private(set) var rates: [String: Double] = [:]
    private var currentField: String = ""
    private var currentCode = ""
    private var currentNominal = ""
    private var currentValue = ""
    private var insideValute = false

    func parser(_ parser: XMLParser, didStartElement elementName: String,
                namespaceURI: String?, qualifiedName qName: String?,
                attributes attributeDict: [String : String] = [:]) {
        if elementName == "Valute" {
            insideValute = true
            currentCode = ""
            currentNominal = ""
            currentValue = ""
        }
        if insideValute { currentField = elementName }
    }

    func parser(_ parser: XMLParser, foundCharacters string: String) {
        guard insideValute else { return }
        switch currentField {
        case "CharCode": currentCode += string
        case "Nominal": currentNominal += string
        case "Value": currentValue += string
        default: break
        }
    }

    func parser(_ parser: XMLParser, didEndElement elementName: String,
                namespaceURI: String?, qualifiedName qName: String?) {
        if elementName == "Valute" {
            let amount = Double(currentValue.replacingOccurrences(of: ",", with: ".")
                .trimmingCharacters(in: .whitespacesAndNewlines))
            let nominal = Double(currentNominal.trimmingCharacters(in: .whitespacesAndNewlines))
            if let amount, let nominal, amount > 0, nominal > 0 {
                rates[currentCode.trimmingCharacters(in: .whitespacesAndNewlines)] = amount / nominal
            }
            insideValute = false
        }
        currentField = ""
    }
}