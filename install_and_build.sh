#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${FINTRACK_DEST:-$HOME/Developer/FinTrack-Mac}"

command -v python3 >/dev/null || { echo 'Нужен python3'; exit 1; }
command -v git >/dev/null || { echo 'Нужен git'; exit 1; }
mkdir -p "$(dirname "$DEST")"
if [[ ! -d "$DEST/.git" ]]; then
  echo "Получаем исходники Mint Leaf v4.2 в $DEST"
  git clone --branch v4.2 --depth 1 https://github.com/Kolomaster68/mint-leaf.git "$DEST"
fi
cd "$DEST"
if [[ -n "$(git status --porcelain)" ]] && [[ ! -f MintLeaf/Localizable.xcstrings ]]; then
  echo "В клоне уже есть незакоммиченные изменения; во избежание потерь остановка."
  exit 2
fi
python3 "$SCRIPT_DIR/apply_ru.py" "$DEST"
echo "Исходники подготовлены в $DEST"

if ! xcodebuild -version >/dev/null 2>&1; then
  echo
  echo "Полный Xcode не найден. Исходники готовы, но локальная сборка невозможна."
  echo "Для сборки без Xcode загрузите репозиторий в GitHub: .github/workflows/build-fintrack-macos.yml"
  exit 0
fi

echo "Собираем FinTrack Mac для Apple Silicon..."
set -o pipefail
xcodebuild -project MintLeaf.xcodeproj -scheme MintLeaf_macOS \
  -configuration Debug -destination 'platform=macOS,arch=arm64' \
  -derivedDataPath .build CODE_SIGNING_ALLOWED=NO build \
  2>&1 | tee "$HOME/Developer/fintrack-build.log" | tail -55
APP="$(find "$DEST/.build/Build/Products/Debug" -maxdepth 1 -name '*.app' -type d -print -quit)"
if [[ -z "$APP" ]]; then
  echo "Не найден собранный .app — см. $HOME/Developer/fintrack-build.log"; exit 3
fi
open "$APP"