# NASDAQ-100 Scraper

Ein Python-Tool zum Abrufen und Speichern der aktuellen NASDAQ-100 Bestandteile von Wikipedia.

## Beschreibung

Dieses Projekt scrapt die Liste der NASDAQ-100 Unternehmen von der Wikipedia-Seite und speichert die Daten in CSV- und JSON-Formaten. Das Tool verwendet mehrere Fallback-Strategien, um eine zuverlässige Datenextraktion zu gewährleisten.

## Features

- **Mehrfache Extraktionsmethoden**: Verwendet sowohl `pandas.read_html()` als auch `BeautifulSoup` als Fallback
- **Robuste Fehlerbehandlung**: Automatische Wiederholungsversuche bei Fehlern
- **Datenvalidierung**: Überprüft die Vollständigkeit und Korrektheit der extrahierten Daten
- **Mehrere Ausgabeformate**: Speichert Daten sowohl als CSV als auch als JSON
- **Logging**: Detaillierte Protokollierung aller Vorgänge
- **Datenbereinigung**: Automatische Bereinigung von Whitespace und Formatierung

## Installation

1. Repository klonen:
```bash
git clone <repository-url>
cd nasdaq100-scraper
```

2. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

## Verwendung

Das Skript direkt ausführen:

```bash
python nasdaq100_scraper.py
```

Das Tool wird automatisch:
1. Die NASDAQ-100 Daten von Wikipedia abrufen
2. Die Daten validieren und bereinigen
3. Die Ergebnisse in `data/nasdaq100_constituents.csv` und `data/nasdaq100_constituents.json` speichern
4. Eine Zusammenfassung der ersten 5 Einträge anzeigen

## Ausgabedateien

- **CSV-Format** (`data/nasdaq100_constituents.csv`): Tabellarische Darstellung für Excel/Spreadsheet-Programme
- **JSON-Format** (`data/nasdaq100_constituents.json`): Strukturierte Daten für programmatische Verwendung

## Datenstruktur

Die extrahierten Daten enthalten folgende Spalten:
- **Ticker**: Börsensymbol des Unternehmens
- **Company**: Vollständiger Firmenname
- **GICS_Sector**: Global Industry Classification Standard Sektor
- **GICS_Sub_Industry**: GICS Unterbranche

## Beispieldaten

Das Tool extrahiert derzeit 101 Unternehmen, darunter:
- Apple Inc. (AAPL) - Information Technology
- Microsoft (MSFT) - Information Technology
- Amazon (AMZN) - Consumer Discretionary
- Nvidia (NVDA) - Information Technology
- Meta Platforms (META) - Communication Services

## Technische Details

### Extraktionsmethoden

1. **Pandas-Methode**: Versucht zuerst `pandas.read_html()` für schnelle Tabellenextraktion
2. **BeautifulSoup-Fallback**: Bei Fehlern der Pandas-Methode wird BeautifulSoup verwendet
3. **Intelligente Spaltenerkennung**: Automatische Identifikation der relevanten Tabellenspalten
4. **Retry-Mechanismus**: Bis zu 3 Wiederholungsversuche bei Netzwerkfehlern

### Datenvalidierung

- Überprüfung auf mindestens 90 Unternehmen (typisch sind ~100-101)
- Validierung aller erforderlichen Spalten
- Bereinigung von Whitespace und Formatierungsfehlern
- Ticker-Validierung (1-5 Großbuchstaben)

## Abhängigkeiten

- `pandas>=1.3.0`: Datenmanipulation und CSV-Export
- `requests>=2.25.0`: HTTP-Anfragen
- `beautifulsoup4>=4.9.0`: HTML-Parsing als Fallback
- `lxml>=4.6.0`: XML/HTML-Parser für pandas
- `html5lib>=1.1`: Zusätzlicher HTML-Parser

## Lizenz und Datenquelle

### Datenquelle
Die Daten werden von der Wikipedia-Seite "NASDAQ-100" abgerufen:
- **Quelle**: [Wikipedia - NASDAQ-100](https://en.wikipedia.org/wiki/Nasdaq-100)
- **Lizenz**: Die Wikipedia-Inhalte stehen unter der [Creative Commons Attribution-ShareAlike License 3.0 (CC BY-SA 3.0)](https://creativecommons.org/licenses/by-sa/3.0/)

### Hinweise zur Nutzung der Wikipedia-Daten
- Die Daten stammen aus Wikipedia und unterliegen der CC BY-SA 3.0 Lizenz
- Bei Weiterverwendung muss Wikipedia als Quelle genannt werden
- Abgeleitete Werke müssen unter derselben Lizenz veröffentlicht werden
- Die Daten werden "wie besehen" bereitgestellt ohne Gewähr für Vollständigkeit oder Aktualität
- Für Finanzentscheidungen sollten offizielle Quellen konsultiert werden

## Fehlerbehebung

### Häufige Probleme

1. **Netzwerkfehler**: Das Tool wiederholt automatisch bei temporären Verbindungsproblemen
2. **Tabellenstruktur geändert**: Bei Änderungen der Wikipedia-Seite kann eine Anpassung der Spaltenerkennungslogik nötig sein
3. **Abhängigkeiten fehlen**: Stellen Sie sicher, dass alle Pakete aus `requirements.txt` installiert sind

### Debug-Informationen

Das Tool protokolliert detailliert alle Schritte. Bei Problemen prüfen Sie die Konsolen-Ausgabe für spezifische Fehlermeldungen.

### Typische Ausgabe
```
2025-06-22 08:27:58,468 - INFO - Attempt 1 of 3
2025-06-22 08:27:58,468 - INFO - Trying to retrieve data with pandas.read_html()...
2025-06-22 08:27:58,750 - WARNING - No suitable Components table found with pandas
2025-06-22 08:27:58,750 - INFO - Falling back to BeautifulSoup...
2025-06-22 08:27:59,078 - INFO - DataFrame validation successful
2025-06-22 08:27:59,078 - INFO - Successfully retrieved 101 components with BeautifulSoup
```

## Projektstruktur

```
nasdaq100-scraper/
├── nasdaq100_scraper.py    # Hauptskript
├── requirements.txt        # Python-Abhängigkeiten
├── README.md              # Diese Datei
└── data/                  # Ausgabeverzeichnis
    ├── nasdaq100_constituents.csv
    └── nasdaq100_constituents.json
```

## Beitragen

Verbesserungen und Bugfixes sind willkommen! Bitte erstellen Sie einen Pull Request oder öffnen Sie ein Issue.

## Haftungsausschluss

Dieses Tool dient nur zu Informationszwecken. Die Daten stammen aus Wikipedia und können unvollständig oder veraltet sein. Für Investitionsentscheidungen konsultieren Sie bitte offizielle Finanzquellen wie NASDAQ oder Bloomberg.
