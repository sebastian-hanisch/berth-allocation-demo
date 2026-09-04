# Kaiplatz-Zuteilung (Berth Allocation) – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-berth-allocation-demo.streamlit.app/)**

Interaktive Demo zum **Berth Allocation Problem (BAP)** aus dem Containerterminal-Betrieb:
welches Schiff legt **wann** und **wo entlang des Kais** an? Schiffe haben eine physische Länge
und belegen einen zusammenhängenden Kai-Abschnitt - zwei Schiffe dürfen sich nie gleichzeitig
überlappen (inkl. Sicherheitsabstand), tiefgängige Schiffe brauchen zusätzlich eine ausreichend
tiefe Wasserzone, und nicht jedes Schiff ist gleich wichtig (Mainliner mit Anschlussverkehr vor
Feeder und Tramp). Teil des Portfolios für die Website "Sebastian Hanisch – Operations Research
und Machine Learning", entstanden als spekulative Demo zu einer allgemein gehaltenen
Terminal-Optimierungs-Ausschreibung (Requirements Engineering + Algorithmen/Constraint-basierte
Optimierung für Container-Terminal-Software).

## Warum dieses Problem

Berth Allocation ist DAS klassische, terminal-weite Optimierungsproblem (Cordeau et al. 2005) -
und deckt eine bislang fehlende Nische im Portfolio ab: **kontinuierliches 2D-Packen im
Zeit-Position-Raum**, statt Zuordnung zu diskreten, unabhängigen Slots wie bei der
Tor-Zuordnung (`dock-demo`). Bewusste Abgrenzung zu [`quaycrane-demo`](../quaycrane-demo)
(gleiches Terminal-Thema, andere Ebene): dort wird entschieden, welche Containerbrücke welche
Bay EINES bereits liegenden Schiffs übernimmt; hier eine Ebene darüber, WANN und WO jedes Schiff
überhaupt anlegt. Handling-Dauer ist hier bewusst fix (nicht crane-count-abhängig) - genau die
Verbindung, die die beiden Demos in der App-Beschreibung benennen.

## Modellierung

Ein Kai der Länge $L$ ist in zwei Tiefenzonen unterteilt (Tiefwasser/Flachwasser, je mit eigenem
Tiefgang-Limit). Jedes Schiff hat Länge, Tiefgang, frühestmögliche Ankunft, feste Liegezeit und
ein Prioritätsgewicht (Mainliner 3×, Feeder 1,5×, Tramp 1×). Entscheidungsvariablen: Startzeit
und Kai-Position, mit der Nebenbedingung, dass sich zwei zeitlich überlappende Schiffe nie
räumlich überlappen (inkl. Sicherheitsabstand), und jedes Schiff vollständig in einer für seinen
Tiefgang zulässigen Zone liegt. Formale Herleitung im Expander "📐 Mathematische Formulierung"
der App.

## Methodik – drei Verfahren im Vergleich

- **FCFS (Ankunftsreihenfolge)**: Schiffe strikt nach Ankunft eingeplant, ohne Rücksicht auf
  Priorität - Baseline.
- **Prioritätsbasiert**: Schiffe nach Prioritätsgewicht (dann Ankunft) eingeplant - Mainliner
  sichern sich zuerst die besten Slots.
- **Prioritätsbasiert + lokale Suche**: startet bei der besseren der beiden Konstruktionen und
  verbessert iterativ per paarweisem Tausch der Einplanungsreihenfolge - nachweislich nie
  schlechter als der Startpunkt.
- **Exakt** (Google OR-Tools CP-SAT, `AddNoOverlap2D`): Referenz und Cross-Check. Läuft bewusst
  nur auf Klick, nicht automatisch bei jeder Regler-Änderung mit.

Die Primäransicht zeigt **dynamisch** die bei den aktuellen Reglereinstellungen tatsächlich beste
Methode (nach gewichteter Wartezeit) - keine wird pauschal bevorzugt.

## Design-Entscheidung: reine Ganzzahlen statt Skalierung

`quaycrane-demo` brauchte für sein CP-SAT-Modell eine Skalierung stetiger Minutenwerte in
Ganzzahlen und stieß dabei auf mehrere, mühsam gefundene Rundungsfehler (`round()` rundete
gelegentlich ab, `check_feasible` und der Solver konnten dadurch knapp auseinanderlaufen - siehe
dortiges README). Diese Demo umgeht die ganze Fehlerklasse von vornherein: Länge, Tiefgang-
Grenzen, Ankunft und Liegezeit werden bereits in `berth_scenario.generate_instance` als echte
Ganzzahlen (Meter, Stunden) erzeugt. Heuristik, unabhängige Prüfung und CP-SAT-Modell arbeiten
alle drei mit denselben Ganzzahlen - keine Skalierung, keine Rundungsdifferenz möglich.

## Design-Entscheidung: `AddNoOverlap2D` statt handgeschriebener Reihenfolge-Constraints

`quaycrane-demo`s CP-SAT-Modell brauchte für ein oberflächlich ähnliches Problem (Nichtüberlappung
mehrerer Ressourcen) hunderte Zeilen handgeschriebener paarweiser Reihenfolge-Constraints, weil
Containerbrücken sich zusätzlich physisch nicht überholen dürfen und auch WÄHREND der Fahrt
zwischen Aufgaben Konflikte erzeugen können (siehe dortiges README für die Fund-Historie). Hier
gibt es keine Fahrt zwischen Positionen und keine Reihenfolge auf einer gemeinsamen Schiene, nur
reine Rechteck-Nichtüberlappung im Zeit-Position-Raum - dafür bietet OR-Tools CP-SAT mit
`AddNoOverlap2D` eine eingebaute, in einer Zeile nutzbare Constraint. Ergebnis: das Modell in
[berth_cp_solver.py](berth_cp_solver.py) löst selbst die größte in der App mögliche Instanz (10
Schiffe) durchweg in unter 200 ms, bewiesen optimal - ganz ohne die iterative Fund-und-Fix-Serie,
die `quaycrane-demo`s Modell brauchte.

## Fund: Preset-Parameter können ein Szenario trivial unlösbar machen, ohne dass das am Regler sichtbar ist

Beim Entwurf des Presets "Mainliner-Stoßzeit trifft Tiefwasser-Engpass" (ursprünglich Kailänge
550 m, Tiefwasserzone-Anteil 30 %, Ø Schiffslänge 220 m) meldete
`Instance.is_trivially_infeasible()` sofort `True`: die Tiefwasserzone war mit 165 m schmaler als
ein einzelnes durchschnittliches Schiff plus Sicherheitsabstand (220 + 15 = 235 m) - unabhängig
von jeder Zeitplanung konnte damit **kein** Schiff dieser Größe dort je anlegen. Kein Bug im
Solver oder in der Heuristik, sondern eine Inkonsistenz zwischen den Preset-Parametern selbst.

**Fix:** Kailänge auf 700 m und Tiefwasserzone-Anteil auf 40 % erhöht (280 m Tiefwasserzone),
Ø Schiffslänge auf 200 m gesenkt - damit passt jedes einzelne Schiff sicher hinein, während die
Zone insgesamt (280 m gegen typischerweise 5-6 gleichzeitig tiefgängige Schiffe à ~215 m
Belegungsbreite) trotzdem eng genug bleibt, um echte Warteschlangen zu erzeugen. Seed 1 liefert
dabei einen besonders klaren Beleg für den Priorität-Tradeoff: Ø Mainliner-Wartezeit sinkt von
41,0 h (FCFS) auf 8,3 h (prioritätsbasiert), während Feeder (9,0 h → 54,0 h) und Tramp
(30,0 h → 75,0 h) im Schnitt deutlich länger warten - dasselbe Prinzip, das die
"📐 Was kostet Mainliner-Priorität die anderen Schiffe?"-Sektion der App live nachrechnet.
`test_generate_instance_presets_are_not_trivially_infeasible` und
`test_presets_produce_feasible_plans` (`tests/`) verhindern eine Wiederholung.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Hauptablauf: Presets im Hauptbereich, Sidebar-Einstellungen, Primäransicht, Kernfrage-Sektion ("Was kostet Mainliner-Priorität die anderen Schiffe?"), Methodenvergleich, Formulierungs-Expander |
| `berth_constants.py` | Defaults, Regler-Grenzen, `PRESETS` |
| `berth_presets.py` | `SettingSpec`/`SETTING_SPECS`, Permalink-Logik, Presets, Zufalls-Seed-Button |
| `berth_scenario.py` | `Zone`/`Ship`/`Instance`, Zufallsflotte, Trivial-Unlösbarkeitsprüfung |
| `berth_evaluation.py` | Unabhängige Machbarkeitsprüfung (`check_feasible`), Kennzahlen (`evaluate`) - von Heuristik UND Solver gleichermaßen genutzt |
| `berth_heuristic.py` | FCFS-, Prioritäts-Konstruktion (Einfüge-Heuristik) und lokale Suche |
| `berth_cp_solver.py` | Exakter CP-SAT-Löser (Google OR-Tools, `AddNoOverlap2D`) |
| `berth_visualization.py` | Kaibelegungs-Chart (Kernvisual, Rechtecke im Zeit-Position-Raum), Methodenvergleich |
| `berth_pdf_export.py` | PDF-Belegungsplan (`fpdf2`) |
| `berth_ui_panel.py` | Wiederverwendbares Panel je Methode im Methodenvergleich-Expander |
| `tests/` | Machbarkeitsprüfung (inkl. handgebauter Verletzungsfälle), Heuristik-Eigenschaften über zufällige Szenarien, CP-SAT-Cross-Check |

## Bewusst nicht umgesetzt (mögliche Erweiterungen)

- **Tidenfenster**: manche Schiffe könnten nur zu bestimmten Zeiten ein-/auslaufen (abhängig von
  Wasserstand). Würde die Startzeit-Domäne jedes Schiffs auf periodische Fenster einschränken.
- **Kranzahl-abhängige Liegezeit**: die Liegezeit ist hier bewusst fix, nicht davon abhängig, wie
  viele Containerbrücken tatsächlich zugewiesen werden - dieses Detail überlässt die Demo bewusst
  [`quaycrane-demo`](../quaycrane-demo), um Modell und Verantwortung sauber zu trennen.

## Lokal ausführen

```bash
pip install -r requirements-dev.txt
streamlit run app.py
```

Tests: `pytest tests/ -v`

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
