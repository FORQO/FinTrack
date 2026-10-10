#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
{
  printf 'import Foundation\nimport FoundationXML\n'
  cat "$HERE/CBRParser.swift.txt"
  cat <<'SWIFT'
let sample = "<ValCurs><Valute><CharCode>USD</CharCode><Nominal>1</Nominal><Value>93,5000</Value></Valute><Valute><CharCode>EUR</CharCode><Nominal>10</Nominal><Value>1017,0000</Value></Valute></ValCurs>"
let reader = FinTrackCBRRateReader()
let parser = XMLParser(data: Data(sample.utf8))
parser.delegate = reader
precondition(parser.parse())
precondition(reader.rates["USD"] == 93.5)
precondition(reader.rates["EUR"] == 101.7)
print("CBR parser: PASS (USD 93.5 RUB, EUR 101.7 RUB per unit)")
SWIFT
} > "$TMP/main.swift"
swiftc -swift-version 6 "$TMP/main.swift" -o "$TMP/cbr-test"
"$TMP/cbr-test"