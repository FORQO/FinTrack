<p align="center">
  <img src=".github/forqo-banner.svg" alt="FinTrack Mac · FORQO — Личные финансы на русском — в приложении для Mac." width="100%">
</p>

<p align="center"><b>Счета, операции, категории и дашборд в RUB, USD и EUR.</b></p>

<p align="center"><a href="#быстрый-старт">Быстрый старт</a> · <a href="#возможности">Возможности</a> · <a href="#разработка">Разработка</a> · <a href="#данные-и-ограничения">Ограничения</a> · <a href="downloads/">Загрузки</a></p>

| Платформа / направление | Статус | Технологии |
| :--- | :--- | :--- |
| macOS 14+ · Apple Silicon | В разработке · сборки для проверки | Swift · SwiftUI · SwiftData |

---

## О проекте

**FinTrack Mac** — русскоязычная модификация [Mint Leaf 4.2](https://github.com/Kolomaster68/mint-leaf), созданная на Swift, SwiftUI и SwiftData. Проект адаптирует интерфейс и финансовый дашборд для работы с рублями, долларами и евро.

> **В разработке.** Сборки требуют проверки на реальном Mac. Приложение пока не подписано Apple Developer ID и не нотарифицировано. Храните резервные копии финансовых данных.

## Возможности

- Дашборд с балансом, активами, обязательствами и денежными потоками.
- Счета, операции, категории и ближайшие платежи.
- Русский каталог интерфейса и рубль как валюта по умолчанию.
- **RUB, USD и EUR** в списках выбора валют.
- Пересчёт совокупных показателей по курсам ЦБ РФ с предупреждением о неактуальных данных.
- Отдельный идентификатор `com.maxliv234.fintrackru`, изолирующий приложение от исходного Mint Leaf.

Базовые возможности наследуются от Mint Leaf. Изменения FinTrack находятся в патч-скриптах, шаблонах Swift и производном проекте в этом репозитории.

## Быстрый старт

**Целевая платформа:** macOS 14+ на Mac с Apple Silicon.

Готовые файлы текущей сборки находятся в [каталоге downloads](downloads):

- [FinTrack-Mac-Apple-Silicon.dmg](https://github.com/FORQO/FinTrack/raw/refs/heads/main/downloads/FinTrack-Mac-Apple-Silicon.dmg)
- [FinTrack-Mac-Apple-Silicon.zip](https://github.com/FORQO/FinTrack/raw/refs/heads/main/downloads/FinTrack-Mac-Apple-Silicon.zip)

Альтернативный источник — [GitHub Actions](https://github.com/FORQO/FinTrack/actions/workflows/build-fintrack-macos.yml): откройте успешный запуск и скачайте артефакт **FinTrack-Mac-Apple-Silicon**, если он ещё доступен. Для скачивания артефактов требуется вход в GitHub.

Отдельный стабильный релиз пока не опубликован. macOS может предупреждать о неподписанной сборке; не отключайте Gatekeeper глобально.

## Разработка

Требуются macOS, Git, Python 3 и полный Xcode с поддержкой Swift 6. Конфигурация проекта указывает Xcode 26.0; workflow использует Xcode из образа `macos-latest`.

```bash
git clone https://github.com/FORQO/FinTrack.git
cd FinTrack
bash install_and_build.sh
```

Скрипт получает Mint Leaf `v4.2`, применяет изменения и собирает приложение для Apple Silicon. Рабочая копия по умолчанию создаётся в `~/Developer/FinTrack-Mac`. Без полного Xcode скрипт только подготавливает исходники.

**Воспроизводимая CI-сборка:** workflow проверяет базовый SHA `9731ed052196a9387527661530df791ef9011d8e`, применяет патчи, запускает проверки и создаёт ZIP / DMG. Производные Swift-исходники уже включены в репозиторий; workflow сборки не коммитит их обратно. Отдельный workflow публикации обновляет файлы в `downloads/`.

## Структура проекта

| Путь | Назначение |
| :--- | :--- |
| `MintLeaf/` | Производные исходники приложения |
| `MintLeaf.xcodeproj/` | Xcode-проект |
| `apply_ru.py` | Применение русификации и изменений FinTrack |
| `base_translations.py`, `extra_translations.py` | Переводы интерфейса |
| `FinTrackDashboard.swift` | Шаблон финансового дашборда |
| `CBRParser.swift.txt`, `CBRRefresh.swift.txt` | Swift-шаблоны для патч-скриптов |
| `tests/`, `MintLeafTests/` | Проверки патчей и финансовой логики |
| `downloads/` | Готовые файлы сборки |
| `.github/workflows/` | Сборка, проверки и подготовка релизов |

Имена `MintLeaf` в исходниках сохранены для совместимости с базовым проектом.

## Проверки

```bash
python3 -m unittest discover -s tests -v
bash tests/verify_cbr_parser.sh
```

Вторая команда требует Swift-компилятор. CI дополнительно запускает XCTest и сборку для arm64.

## Данные и ограничения

- Текущие курсы на исторических графиках дают ориентировочную оценку, а не бухгалтерский курс конкретной даты.
- При недоступности актуального курса используются закешированные или резервные ставки.
- Полноту перевода динамических сообщений ещё нужно проверить; актуальный статический аудит — в [отчёте локализации](LOCALIZATION_REPORT_RU.md).
- Существующие счета в других валютах сохраняют историю.
- Банковские выписки, резервные копии, токены и персональные операции не следует добавлять в Git или публичные Issues.

## Обратная связь

Для ошибки укажите версию macOS, модель Mac, номер сборки и шаги воспроизведения. Для проблем с суммами или курсами приложите небольшой искусственный пример без реальных финансовых данных.

[Сообщить об ошибке или предложить улучшение](https://github.com/FORQO/FinTrack/issues).

## Происхождение и лицензия

Основа — [Mint Leaf 4.2](https://github.com/Kolomaster68/mint-leaf/tree/v4.2), © 2026 Joe Farmer. FinTrack Mac — независимая русскоязычная модификация. Исходная [MIT License](LICENSE) и авторские уведомления сохранены.

---

<p align="center"><sub><a href="https://github.com/FORQO"><b>FORQO</b></a> · SOFTWARE ENGINEERING<br>Desktop applications · Open source · RU interfaces</sub></p>
